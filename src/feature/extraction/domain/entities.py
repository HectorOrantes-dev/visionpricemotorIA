from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Dimensiones(BaseModel):
    """Medidas normalizadas en metros. El back-end usa esto para calcular
    cantidades (cajas, bultos) con su catálogo; el ML no hace cálculos."""
    area_m2: Optional[float] = None        # área a cubrir
    largo_m: Optional[float] = None
    ancho_m: Optional[float] = None
    alto_m: Optional[float] = None
    pieza_largo_m: Optional[float] = None  # tamaño de la pieza (ej. loseta 1x1)
    pieza_ancho_m: Optional[float] = None

class ExtractionResult(BaseModel):
    ubicacion: Optional[str] = None
    tipo_superficie: Optional[str] = None
    materiales: List[str] = []
    colores: List[str] = []
    dimensiones: Dimensiones = Field(default_factory=Dimensiones)
    dimensiones_crudo: List[str] = []

class ExtractionRecord(BaseModel):
    id: str
    grabacion_id: str
    proyecto_id: str
    audio_url: str
    transcription: str
    extracted_data: ExtractionResult
    created_at: datetime

    @classmethod
    def create(cls, grabacion_id: str, proyecto_id: str, audio_url: str, transcription: str, extracted_data: ExtractionResult) -> 'ExtractionRecord':
        return cls(
            id=str(uuid.uuid4()),
            grabacion_id=grabacion_id,
            proyecto_id=proyecto_id,
            audio_url=audio_url,
            transcription=transcription,
            extracted_data=extracted_data,
            created_at=datetime.utcnow()
        )
