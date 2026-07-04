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
    # Vocabulario de dominio para el corrector de transcripción (Fase 1)
    VOCAB_PATH: str = os.getenv("VOCAB_PATH", "./dominio_vocab.json")
    
    # Almacenamiento de audios
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # Autenticación entre microservicios
    MICROSERVICE_API_KEY: str = os.getenv("MICROSERVICE_API_KEY", "visionprice-secret-key-2024")
    
    # API
    API_PREFIX: str = "/api/v1"

    # CORS: única URL del back-end que puede consumir esta API
    ALLOWED_ORIGIN: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")

    # Object storage (Cloudflare R2 - compatible con S3)
    R2_ENDPOINT_URL: str = os.getenv("R2_ENDPOINT_URL", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET: str = os.getenv("R2_BUCKET", "")
    # URL pública del bucket (dominio R2 o custom). Si se deja vacía, audio_url
    # guardará solo la key del objeto.
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")
    # Prefijo (carpeta) dentro del bucket donde vive el modelo BETO en R2.
    R2_MODEL_PREFIX: str = os.getenv("R2_MODEL_PREFIX", "models/beto_visionprice")

    # Callback hacia el back-end principal (flujo asíncrono)
    ML_CALLBACK_URL: str = os.getenv("ML_CALLBACK_URL", "")  # URL completa, ej: https://backend/api/v1/ml/callback
    ML_CALLBACK_API_KEY: str = os.getenv("ML_CALLBACK_API_KEY", "")

settings = Settings()
