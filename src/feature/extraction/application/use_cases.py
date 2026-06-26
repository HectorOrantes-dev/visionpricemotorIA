import os

from src.feature.extraction.domain.entities import ExtractionRecord
from src.feature.extraction.domain.repositories import (
    IAudioTranscriber,
    IEntityExtractor,
    IExtractionRepository,
    IObjectStorage,
    IMlCallbackNotifier,
)


class ProcessAudioUseCase:
    def __init__(
        self,
        transcriber: IAudioTranscriber,
        extractor: IEntityExtractor,
        repository: IExtractionRepository,
        storage: IObjectStorage,
        notifier: IMlCallbackNotifier,
    ):
        self.transcriber = transcriber
        self.extractor = extractor
        self.repository = repository
        self.storage = storage
        self.notifier = notifier

    def execute(self, grabacion_id: str, proyecto_id: str, audio_path: str, file_ext: str) -> None:
        """
        Flujo asíncrono del motor de IA (corre en background):
        1. Sube el audio al object storage (R2).
        2. Transcribe el audio con Whisper.
        3. Extrae las entidades con BETO.
        4. Guarda el resultado en PostgreSQL.
        5. Notifica al back-end principal vía callback (POST con X-Api-Key).

        Cualquier error se reporta también por callback con status="failed".
        Nunca relanza: es una tarea de fondo y no hay nadie esperando la respuesta.
        """
        audio_url = ""
        try:
            # 1. Subir el audio a R2
            object_key = f"grabaciones/{proyecto_id}/{grabacion_id}{file_ext}"
            audio_url = self.storage.upload(audio_path, object_key)

            # 2. Transcripción (Whisper) - usa el archivo temporal local
            transcription_text = self.transcriber.transcribe(audio_path)

            # 3. Extracción (BETO)
            extracted_data = self.extractor.extract_entities(transcription_text)

            # 4. Guardado en PostgreSQL
            record = ExtractionRecord.create(
                grabacion_id=grabacion_id,
                proyecto_id=proyecto_id,
                audio_url=audio_url,
                transcription=transcription_text,
                extracted_data=extracted_data,
            )
            self.repository.save(record)

            # 5. Callback de éxito
            self.notifier.notify({
                "grabacion_id": grabacion_id,
                "proyecto_id": proyecto_id,
                "status": "completed",
                "audio_url": audio_url,
                "transcription": transcription_text,
                "extracted_data": extracted_data.model_dump(),
                "error": None,
            })
        except Exception as e:
            print(f"❌ Error procesando grabacion {grabacion_id}: {e}")
            self.notifier.notify({
                "grabacion_id": grabacion_id,
                "proyecto_id": proyecto_id,
                "status": "failed",
                "audio_url": audio_url,
                "transcription": None,
                "extracted_data": None,
                "error": str(e),
            })
        finally:
            # Limpiar el archivo temporal local
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
