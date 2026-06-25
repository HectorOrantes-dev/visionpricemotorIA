import whisper
from src.feature.extraction.domain.repositories import IAudioTranscriber

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
        result = self.model.transcribe(audio_path, language="es")
        return result["text"].strip()
