from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from src.core.config import settings
from src.core.database import engine

# Adaptadores (Infraestructura)
from src.feature.extraction.infrastructure.adapters.whisper_adapter import WhisperAdapter
from src.feature.extraction.infrastructure.adapters.beto_adapter import BetoAdapter
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

    # 4. Construir el Caso de Uso inyectando las dependencias
    use_case = ProcessAudioUseCase(
        transcriber=whisper_adapter,
        extractor=beto_adapter,
        repository=repository
    )

    # 5. Inyectar el caso de uso en el controlador
    extraction_controller.init_controller(use_case=use_case, repository=repository)

    # 6. Crear carpeta de uploads si no existe
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

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

# Servir archivos de audio estáticamente para que el usuario pueda reproducirlos
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ============================================================================
# Endpoint de Salud
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "VisionPrice AI Engine", "version": "1.0.0"}
