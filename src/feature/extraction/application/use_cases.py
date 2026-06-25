from src.feature.extraction.domain.entities import ExtractionRecord
from src.feature.extraction.domain.repositories import IAudioTranscriber, IEntityExtractor, IExtractionRepository

class ProcessAudioUseCase:
    def __init__(
        self,
        transcriber: IAudioTranscriber,
        extractor: IEntityExtractor,
        repository: IExtractionRepository
    ):
        self.transcriber = transcriber
        self.extractor = extractor
        self.repository = repository

    def execute(self, user_hash: str, audio_path: str) -> ExtractionRecord:
        """
        Orquesta el flujo principal del motor de IA:
        1. Convierte el audio a texto con Whisper.
        2. Extrae las entidades con BETO.
        3. Guarda el resultado en la base de datos asociado al usuario.
        """
        # 1. Transcripción (Whisper)
        transcription_text = self.transcriber.transcribe(audio_path)
        
        # 2. Extracción (BETO)
        extracted_data = self.extractor.extract_entities(transcription_text)
        
        # 3. Guardado en Base de Datos (PostgreSQL)
        record = ExtractionRecord.create(
            user_hash=user_hash,
            audio_url=audio_path, # En el futuro, esto será la URL de S3
            transcription=transcription_text,
            extracted_data=extracted_data
        )
        saved_record = self.repository.save(record)
        
        return saved_record
