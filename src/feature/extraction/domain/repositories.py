from abc import ABC, abstractmethod
from typing import List, Optional
from src.feature.extraction.domain.entities import ExtractionRecord, ExtractionResult

class IAudioTranscriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Convierte un archivo de audio (.wav/.m4a) a texto usando Whisper"""
        pass

class IEntityExtractor(ABC):
    @abstractmethod
    def extract_entities(self, text: str) -> ExtractionResult:
        """Toma el texto de Whisper y usa BETO para extraer el JSON de materiales"""
        pass

class IExtractionRepository(ABC):
    @abstractmethod
    def save(self, record: ExtractionRecord) -> ExtractionRecord:
        """Guarda un ExtractionRecord en la base de datos"""
        pass

    @abstractmethod
    def get_by_user_hash(self, user_hash: str) -> List[ExtractionRecord]:
        """Obtiene todas las extracciones asociadas a un usuario"""
        pass
