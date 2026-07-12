from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from src.feature.extraction.domain.entities import ExtractionRecord, ExtractionResult, ExtractionItem, Dimensiones

class IAudioTranscriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """Convierte un archivo de audio (.wav/.m4a) a texto usando Whisper"""
        pass

class IEntityExtractor(ABC):
    @abstractmethod
    def extract_entities(self, text: str) -> ExtractionItem:
        """Usa BETO para extraer superficie, materiales, colores y ubicación de un texto"""
        pass


class ITextCorrector(ABC):
    @abstractmethod
    def correct(self, text: str) -> str:
        """Corrige errores de transcripción contra el vocabulario de dominio"""
        pass


class IDimensionExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> Tuple[Dimensiones, List[str]]:
        """Extrae medidas normalizadas del texto. Devuelve (Dimensiones, crudo)."""
        pass

class ICategoryClassifier(ABC):
    @abstractmethod
    def classify(self, tipo_superficie: Optional[str], materiales: List[str], texto: str = "") -> Optional[str]:
        """Deriva la categoría de producto (piso, azulejo, zoclo, pintura...)
        a partir de la superficie y los materiales detectados. `texto` es el
        segmento crudo, usado como respaldo cuando no se detectó material."""
        pass


class IExtractionRepository(ABC):
    @abstractmethod
    def save(self, record: ExtractionRecord) -> ExtractionRecord:
        """Guarda un ExtractionRecord en la base de datos"""
        pass

    @abstractmethod
    def get_by_proyecto_id(self, proyecto_id: str) -> List[ExtractionRecord]:
        """Obtiene todas las extracciones asociadas a un proyecto"""
        pass


class IObjectStorage(ABC):
    @abstractmethod
    def upload(self, local_path: str, object_key: str) -> str:
        """Sube un archivo al object storage y devuelve la URL pública (o la key)"""
        pass


class IMlCallbackNotifier(ABC):
    @abstractmethod
    def notify(self, payload: dict) -> None:
        """Notifica al back-end principal el resultado del procesamiento (POST con X-Api-Key)"""
        pass
