import whisper
from src.feature.extraction.domain.repositories import IAudioTranscriber

# Sesga el decodificado de Whisper hacia el vocabulario de construcción.
# Reduce errores tipo "pared→pareja" o "piso→pizo" sin subir el tamaño del modelo.
DOMAIN_PROMPT = (
    "Presupuesto de construcción. Términos frecuentes: pared, muro, piso, techo, "
    "suelo, fachada, azulejo, porcelanato, loseta, zoclo, pegazulejo, cerámico, "
    "cemento, mortero, crucetas, boquilla. Colores: negro, blanco, gris, beige, "
    "café, hueso. Medidas en metros, por ejemplo 2 por 3 metros."
)

class WhisperAdapter(IAudioTranscriber):
    def __init__(self, model_name="small"):
        print(f"Cargando modelo Whisper ({model_name})...")
        self.model = whisper.load_model(model_name)
        print("✅ Whisper cargado exitosamente.")

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe el archivo de audio (.wav/.m4a) a texto
        """
        print(f"🎙️ Transcribiendo audio: {audio_path}...")
        result = self.model.transcribe(
            audio_path,
            language="es",
            initial_prompt=DOMAIN_PROMPT,
        )
        return result["text"].strip()
