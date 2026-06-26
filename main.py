from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine

# Adaptadores (Infraestructura)
from src.feature.extraction.infrastructure.adapters.whisper_adapter import WhisperAdapter
from src.feature.extraction.infrastructure.adapters.beto_adapter import BetoAdapter
from src.feature.extraction.infrastructure.adapters.r2_storage_adapter import R2StorageAdapter
from src.feature.extraction.infrastructure.adapters.callback_adapter import HttpCallbackAdapter
from src.feature.extraction.infrastructure.repositories.postgres_extraction_repository import (
    PostgresExtractionRepository,
    Base as ExtractionBase
)

# Caso de Uso (Aplicación)
from src.feature.extraction.application.use_cases import ProcessAudioUseCase

# Controladores (Infraestructura)
from src.feature.extraction.infrastructure.controllers import extraction_controller

# ============================================================================
# Lifecycle de la Aplicación (Composición Root - Hexagonal)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Composition Root de la Arquitectura Hexagonal.
    Aquí se construyen todas las dependencias y se inyectan.
    """
    print("🚀 Iniciando VisionPrice Motor de IA...")

    # 1. Crear las tablas en PostgreSQL si no existen
    ExtractionBase.metadata.create_all(bind=engine)
    print("✅ Base de datos PostgreSQL conectada y tablas creadas.")

    # 2. Inicializar Adaptadores de IA
    whisper_adapter = WhisperAdapter(model_name=settings.WHISPER_MODEL)
    beto_adapter = BetoAdapter(model_path=settings.BETO_MODEL_PATH)

    # 3. Inicializar Repositorio de PostgreSQL
    repository = PostgresExtractionRepository(db_url=settings.DATABASE_URL)

    # 4. Inicializar Object Storage (R2) y Notificador de callback
    storage = R2StorageAdapter(
        endpoint_url=settings.R2_ENDPOINT_URL,
        access_key_id=settings.R2_ACCESS_KEY_ID,
        secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        bucket=settings.R2_BUCKET,
        public_url=settings.R2_PUBLIC_URL,
    )
    notifier = HttpCallbackAdapter(
        callback_url=settings.ML_CALLBACK_URL,
        api_key=settings.ML_CALLBACK_API_KEY,
    )

    # 5. Construir el Caso de Uso inyectando las dependencias
    use_case = ProcessAudioUseCase(
        transcriber=whisper_adapter,
        extractor=beto_adapter,
        repository=repository,
        storage=storage,
        notifier=notifier,
    )

    # 6. Inyectar el caso de uso en el controlador
    extraction_controller.init_controller(use_case=use_case, repository=repository)

    print("✅ Motor de IA listo para recibir solicitudes.")
    
    yield  # La app corre aquí
    
    print("🛑 Apagando VisionPrice Motor de IA...")

# ============================================================================
# Inicialización de la Aplicación FastAPI
# ============================================================================

app = FastAPI(
    title="VisionPrice - Motor de IA",
    description="Microservicio para extracción inteligente de materiales de construcción a partir de audio.",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS - Solo el back-end autorizado puede consumir esta API
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Registro de Routers
# ============================================================================

app.include_router(extraction_controller.router, prefix=settings.API_PREFIX)

# ============================================================================
# Endpoint de Salud
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "VisionPrice AI Engine", "version": "1.0.0"}
