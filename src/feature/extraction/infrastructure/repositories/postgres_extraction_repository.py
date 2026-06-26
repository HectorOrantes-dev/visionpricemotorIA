from typing import List
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.feature.extraction.domain.entities import ExtractionRecord, ExtractionResult
from src.feature.extraction.domain.repositories import IExtractionRepository

class Base(DeclarativeBase):
    pass

class ExtractionModel(Base):
    __tablename__ = 'extractions'

    id = Column(String, primary_key=True)
    grabacion_id = Column(String, index=True, nullable=False)
    proyecto_id = Column(String, index=True, nullable=False)
    audio_url = Column(String, nullable=False)
    transcription = Column(String, nullable=False)
    extracted_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False)

class PostgresExtractionRepository(IExtractionRepository):
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save(self, record: ExtractionRecord) -> ExtractionRecord:
        with self.Session() as session:
            db_model = ExtractionModel(
                id=record.id,
                grabacion_id=record.grabacion_id,
                proyecto_id=record.proyecto_id,
                audio_url=record.audio_url,
                transcription=record.transcription,
                extracted_data=record.extracted_data.model_dump(),
                created_at=record.created_at
            )
            session.add(db_model)
            session.commit()
            return record

    def get_by_proyecto_id(self, proyecto_id: str) -> List[ExtractionRecord]:
        with self.Session() as session:
            db_models = session.query(ExtractionModel).filter(ExtractionModel.proyecto_id == proyecto_id).all()

            return [
                ExtractionRecord(
                    id=model.id,
                    grabacion_id=model.grabacion_id,
                    proyecto_id=model.proyecto_id,
                    audio_url=model.audio_url,
                    transcription=model.transcription,
                    extracted_data=ExtractionResult(**model.extracted_data),
                    created_at=model.created_at
                )
                for model in db_models
            ]
