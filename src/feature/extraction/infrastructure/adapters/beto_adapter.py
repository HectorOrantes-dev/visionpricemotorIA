from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from src.feature.extraction.domain.repositories import IEntityExtractor
from src.feature.extraction.domain.entities import ExtractionItem

# Palabras basura que BETO a veces etiqueta por error (ruido de "prueba de audio", etc.)
TOKENS_IGNORADOS = {"audio", "prueba", "pruebas", "la", "el", "los", "las", "un",
                    "una", "unos", "unas", "de", "mío", "mio", "esto", "este"}


class BetoAdapter(IEntityExtractor):
    def __init__(self, model_path="./modelo_beto_visionprice"):
        print(f"Cargando modelo BETO desde {model_path}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForTokenClassification.from_pretrained(model_path)
            self.nlp = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")
            print("✅ Modelo BETO cargado con éxito.")
        except Exception as e:
            print(f"⚠️ Error al cargar el modelo BETO: {e}")
            self.nlp = None

    def extract_entities(self, text: str) -> ExtractionItem:
        if not self.nlp:
            raise RuntimeError("El modelo BETO no está cargado")

        resultados = self.nlp(text)

        item = ExtractionItem(materiales=[], colores=[], dimensiones_crudo=[])

        for entidad in resultados:
            grupo = entidad['entity_group']
            palabra = entidad['word'].strip()

            # Filtrar tokens basura (ruido que BETO etiqueta por error)
            if palabra.lower() in TOKENS_IGNORADOS:
                continue

            if grupo == 'UBICACION':
                item.ubicacion = palabra
            elif grupo == 'SUPERFICIE':
                item.tipo_superficie = palabra
            elif grupo == 'COLOR':
                if palabra not in item.colores:
                    item.colores.append(palabra)
            elif grupo == 'MATERIAL':
                # Normalización de errores comunes de transcripción
                if "pega su lejo" in palabra.lower(): palabra = "pegazulejo"
                if "los z" in palabra.lower() or "los zeta" in palabra.lower(): palabra = "loseta"
                if "soplo" in palabra.lower(): palabra = "zoclo"
                if "por sela" in palabra.lower() or "por cela" in palabra.lower(): palabra = "porcelanato"
                if "azul lejo" in palabra.lower() or "a su lejo" in palabra.lower(): palabra = "azulejo"

                if palabra not in item.materiales:
                    item.materiales.append(palabra)

        return item
