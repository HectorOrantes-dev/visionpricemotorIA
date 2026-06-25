import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/visionprice")
    
    # Modelos de IA
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    BETO_MODEL_PATH: str = os.getenv("BETO_MODEL_PATH", "./modelo_beto_visionprice")
    
    # Almacenamiento de audios
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # Autenticación entre microservicios
    MICROSERVICE_API_KEY: str = os.getenv("MICROSERVICE_API_KEY", "visionprice-secret-key-2024")
    
    # API
    API_PREFIX: str = "/api/v1"

settings = Settings()
