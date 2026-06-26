import os
import shutil
import tempfile
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from typing import List

from src.core.config import settings
from src.feature.extraction.application.use_cases import ProcessAudioUseCase
from src.feature.auth.infraestructure.dependencies.auth_dependency import require_api_key

router = APIRouter(prefix="/extractions", tags=["Extractions"])

# Estas variables se inyectan desde main.py al iniciar la app
_use_case: ProcessAudioUseCase = None
_repository = None

ALLOWED_EXTENSIONS = [".wav", ".m4a", ".mp3", ".ogg"]


def init_controller(use_case: ProcessAudioUseCase, repository):
    """Se llama desde main.py para inyectar las dependencias ya construidas"""
    global _use_case, _repository
    _use_case = use_case
    _repository = repository


@router.post("/", response_model=dict, status_code=202)
async def extract_from_audio(
    background_tasks: BackgroundTasks,
    grabacion_id: str = Form(..., description="ID de la grabación en el back-end principal"),
    proyecto_id: str = Form(..., description="ID del proyecto al que pertenece la grabación"),
    audio: UploadFile = File(..., description="Archivo de audio (.wav, .m4a, .mp3, .ogg)"),
    _api_key: str = Depends(require_api_key)  # 🔒 Protegido con API Key
):
    """
    Recibe un audio y lo procesa de forma ASÍNCRONA.

    REQUIERE el header X-Api-Key para autenticarse.

    Flujo:
    1. Valida y guarda el audio en un archivo temporal.
    2. Encola el procesamiento en segundo plano y responde 202 de inmediato.
    3. En background: sube el audio a R2, transcribe (Whisper), extrae (BETO),
       guarda en PostgreSQL y notifica el resultado vía POST al callback.
    """
    if _use_case is None:
        raise HTTPException(status_code=500, detail="El motor de IA no está inicializado")

    # Validar extensión
    file_ext = os.path.splitext(audio.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {file_ext}. Usa: {ALLOWED_EXTENSIONS}"
        )

    # Guardar el audio en un archivo temporal. Debe persistir más allá de esta
    # petición (lo consume la tarea de fondo), por eso usamos un temp con nombre
    # único en lugar del stream de UploadFile (que se cierra al responder).
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f"{grabacion_id}_{uuid.uuid4().hex[:8]}_", suffix=file_ext)
    try:
        with os.fdopen(tmp_fd, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error guardando el audio: {str(e)}")

    # Encolar el procesamiento pesado en segundo plano
    background_tasks.add_task(
        _use_case.execute,
        grabacion_id=grabacion_id,
        proyecto_id=proyecto_id,
        audio_path=tmp_path,
        file_ext=file_ext,
    )

    return {
        "status": "accepted",
        "grabacion_id": grabacion_id,
        "proyecto_id": proyecto_id,
        "message": "Audio recibido. El resultado se notificará por callback al terminar.",
    }


@router.get("/proyecto/{proyecto_id}", response_model=dict)
async def get_proyecto_extractions(
    proyecto_id: str,
    _api_key: str = Depends(require_api_key)  # 🔒 Protegido con API Key
):
    """
    Devuelve el historial de todas las extracciones de un proyecto.

    REQUIERE el header X-Api-Key para autenticarse.
    """
    if _repository is None:
        raise HTTPException(status_code=500, detail="Repositorio no inicializado")

    records = _repository.get_by_proyecto_id(proyecto_id)

    return {
        "status": "success",
        "proyecto_id": proyecto_id,
        "total": len(records),
        "extractions": [
            {
                "id": r.id,
                "grabacion_id": r.grabacion_id,
                "audio_url": r.audio_url,
                "transcription": r.transcription,
                "extracted_data": r.extracted_data.model_dump(),
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]
    }
