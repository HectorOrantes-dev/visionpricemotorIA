import os
import re

from src.feature.extraction.domain.entities import ExtractionRecord, ExtractionResult, ExtractionItem
from src.feature.extraction.domain.repositories import (
    IAudioTranscriber,
    IEntityExtractor,
    IExtractionRepository,
    IObjectStorage,
    IMlCallbackNotifier,
    ITextCorrector,
    IDimensionExtractor,
)

# Marcadores que indican el inicio de otra superficie dentro del mismo audio
# ("la otra pared", "la segunda", "pared 2", "el tercer piso"...).
SEGMENT_RE = re.compile(
    r"\b(?:la\s+otra|el\s+otro|otra\s+pared|otro\s+piso|otro\s+muro|"
    r"la\s+primera|la\s+segunda|la\s+tercera|la\s+cuarta|"
    r"el\s+primer[oa]?|el\s+segundo|el\s+tercero|el\s+cuarto|"
    r"pared\s*(?:\d+|uno|dos|tres|cuatro)|piso\s*(?:\d+|uno|dos|tres|cuatro)|"
    r"muro\s*(?:\d+|uno|dos|tres|cuatro)|además|también)\b",
    re.IGNORECASE,
)


class ProcessAudioUseCase:
    def __init__(
        self,
        transcriber: IAudioTranscriber,
        extractor: IEntityExtractor,
        repository: IExtractionRepository,
        storage: IObjectStorage,
        notifier: IMlCallbackNotifier,
        corrector: ITextCorrector,
        dimension_extractor: IDimensionExtractor,
        voice_model_label: str = "whisper-small",
        extraction_model_version: str = "beto-visionprice-1.1",
    ):
        self.transcriber = transcriber
        self.extractor = extractor
        self.repository = repository
        self.storage = storage
        self.notifier = notifier
        self.corrector = corrector
        self.dimension_extractor = dimension_extractor
        self.voice_model_label = voice_model_label
        self.extraction_model_version = extraction_model_version

    def execute(self, grabacion_id: str, proyecto_id: str, audio_path: str, file_ext: str) -> None:
        """
        Flujo asíncrono (background):
        1. Sube el audio a R2 y transcribe (Whisper) + corrige el texto.
        2. Extrae entidades (BETO) y dimensiones (regex) -> best effort.
        3. Guarda en PostgreSQL -> best effort.
        4. Notifica al back-end vía callback con el contrato acordado.
        Nunca relanza: es tarea de fondo.
        """
        object_key = f"grabaciones/{proyecto_id}/{grabacion_id}{file_ext}"
        texto = None

        # --- Paso obligatorio: audio + transcripción. Sin 'texto' no hay callback válido. ---
        try:
            self.storage.upload(audio_path, object_key)
            print(f"☁️ Audio subido a R2: {object_key}")
            raw_text = self.transcriber.transcribe(audio_path)
            texto = self.corrector.correct(raw_text)
            if texto != raw_text:
                print(f"✏️ Texto corregido:\n   antes: {raw_text}\n   después: {texto}")
            print(f"📝 Transcripción final (grabacion {grabacion_id}): {texto}")
        except Exception as e:
            print(f"❌ Error en audio/transcripción de grabacion {grabacion_id}: {e}")
            self._cleanup(audio_path)
            # El back-end exige 'texto'; sin transcripción no hay callback útil.
            return

        # --- Extracción multi-superficie (best effort). ---
        extracted = ExtractionResult()
        parametros_json = None
        try:
            extracted = self._extract_items(texto)
            parametros_json = extracted.model_dump()
            print(f"🧩 {len(extracted.items)} superficie(s) detectada(s) "
                  f"(múltiple={extracted.es_multiple}).")
        except Exception as e:
            print(f"⚠️ Extracción (BETO/dimensiones) falló para grabacion {grabacion_id}: {e}. "
                  f"Se enviará solo la transcripción.")

        # --- Guardado en BD (best effort). ---
        try:
            record = ExtractionRecord.create(
                grabacion_id=grabacion_id,
                proyecto_id=proyecto_id,
                audio_url=object_key,
                transcription=texto,
                extracted_data=extracted,
            )
            self.repository.save(record)
        except Exception as e:
            print(f"⚠️ No se pudo guardar en BD la grabacion {grabacion_id}: {e}")

        # --- Callback al back-end principal (contrato acordado). ---
        payload = {
            "grabacion_id": self._to_int(grabacion_id),
            "texto": texto,
            "object_storage_key": object_key,
            "modelo_voice_to_text": self.voice_model_label,
            "version_modelo": self.extraction_model_version,
        }
        if parametros_json is not None:
            payload["parametros_json"] = parametros_json
        print(f"📤 Enviando callback de grabacion {grabacion_id} al back-end...")
        self.notifier.notify(payload)

        self._cleanup(audio_path)

    def _extract_items(self, texto: str) -> ExtractionResult:
        """
        Divide la transcripción en superficies y arma un item por cada medida.
        - Cada segmento con una medida ("2 por 2") es una superficie del presupuesto.
        - El contexto (superficie/color) del intro se hereda a los items siguientes.
        - Si no hay medidas, devuelve un único item con el texto completo.
        """
        segmentos = self._segmentar(texto)
        items = []
        superficie_ctx = None
        colores_ctx = []

        for seg in segmentos:
            base = self.extractor.extract_entities(seg)          # ExtractionItem
            dimensiones, dim_crudo = self.dimension_extractor.extract(seg)

            # Actualizar contexto heredable
            if base.tipo_superficie:
                superficie_ctx = base.tipo_superficie
            if base.colores:
                colores_ctx = base.colores

            # Un segmento es una superficie del presupuesto si trae una medida.
            if dim_crudo:
                base.dimensiones = dimensiones
                base.dimensiones_crudo = dim_crudo
                if not base.tipo_superficie:
                    base.tipo_superficie = superficie_ctx
                if not base.colores:
                    base.colores = list(colores_ctx)
                items.append(base)

        # Sin medidas detectadas: un solo item con todo el texto.
        if not items:
            base = self.extractor.extract_entities(texto)
            dimensiones, dim_crudo = self.dimension_extractor.extract(texto)
            base.dimensiones = dimensiones
            base.dimensiones_crudo = dim_crudo
            items = [base]

        return ExtractionResult(es_multiple=len(items) > 1, items=items)

    @staticmethod
    def _segmentar(texto: str) -> list:
        """Corta el texto en los marcadores de 'otra superficie'. Si no hay, [texto]."""
        starts = [m.start() for m in SEGMENT_RE.finditer(texto)]
        if not starts:
            return [texto]
        cortes = sorted(set([0] + starts + [len(texto)]))
        segs = [texto[cortes[i]:cortes[i + 1]].strip(" ,.") for i in range(len(cortes) - 1)]
        return [s for s in segs if s]

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    @staticmethod
    def _cleanup(audio_path: str) -> None:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass
