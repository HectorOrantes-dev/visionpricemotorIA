from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class ExtractionResult(BaseModel):
    ubicacion: Optional[str] = None
    tipo_superficie: Optional[str] = None
    materiales: List[str] = []
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
