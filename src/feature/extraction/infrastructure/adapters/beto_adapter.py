from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from src.feature.extraction.domain.repositories import IEntityExtractor
from src.feature.extraction.domain.entities import ExtractionResult

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

    def extract_entities(self, text: str) -> ExtractionResult:
        if not self.nlp:
            raise RuntimeError("El modelo BETO no está cargado")

        resultados = self.nlp(text)
        
        extracted = ExtractionResult(materiales=[], dimensiones_crudo=[])
        
        for entidad in resultados:
            grupo = entidad['entity_group']
            palabra = entidad['word']
            
            if grupo == 'UBICACION':
                extracted.ubicacion = palabra
            elif grupo == 'SUPERFICIE':
                extracted.tipo_superficie = palabra
            elif grupo == 'MATERIAL':
                # Normalización
                if "pega su lejo" in palabra.lower(): palabra = "pegazulejo"
                if "los z" in palabra.lower() or "los zeta" in palabra.lower(): palabra = "loseta"
                if "soplo" in palabra.lower(): palabra = "zoclo"
                if "por sela" in palabra.lower() or "por cela" in palabra.lower(): palabra = "porcelanato"
                if "azul lejo" in palabra.lower() or "a su lejo" in palabra.lower(): palabra = "azulejo"
                
                if palabra not in extracted.materiales:
                    extracted.materiales.append(palabra)
            elif grupo == 'DIMENSION':
                extracted.dimensiones_crudo.append(palabra)
                
        return extracted
