import os
from dotenv import load_dotenv

load_dotenv()


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/visionprice")
    # Railway/Heroku a veces entregan el esquema antiguo postgres://,
    # que SQLAlchemy 2.0 no acepta (necesita postgresql://).
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    # Base de datos
    DATABASE_URL: str = _get_database_url()
    
    # Modelos de IA
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    BETO_MODEL_PATH: str = os.getenv("BETO_MODEL_PATH", "./modelo_beto_visionprice")
    
    # Almacenamiento de audios
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # Autenticación entre microservicios
    MICROSERVICE_API_KEY: str = os.getenv("MICROSERVICE_API_KEY", "visionprice-secret-key-2024")
    
    # API
    API_PREFIX: str = "/api/v1"

    # CORS: única URL del back-end que puede consumir esta API
    ALLOWED_ORIGIN: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")

settings = Settings()
