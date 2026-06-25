import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List

from src.core.config import settings
from src.feature.extraction.domain.entities import ExtractionRecord
from src.feature.extraction.application.use_cases import ProcessAudioUseCase
from src.feature.auth.infraestructure.dependencies.auth_dependency import require_api_key

router = APIRouter(prefix="/extractions", tags=["Extractions"])

# Estas variables se inyectan desde main.py al iniciar la app
_use_case: ProcessAudioUseCase = None
_repository = None

def init_controller(use_case: ProcessAudioUseCase, repository):
    """Se llama desde main.py para inyectar las dependencias ya construidas"""
    global _use_case, _repository
    _use_case = use_case
    _repository = repository

@router.post("/", response_model=dict, status_code=201)
async def extract_from_audio(
    user_hash: str = Form(..., description="Hash único del usuario"),
    audio: UploadFile = File(..., description="Archivo de audio (.wav, .m4a)"),
    _api_key: str = Depends(require_api_key)  # 🔒 Protegido con API Key
):
    """
    Recibe un archivo de audio y el user_hash del usuario.
    
    REQUIERE el header X-Api-Key para autenticarse.
    Tu API principal envía este header automáticamente.
    
    1. Guarda el audio en /uploads/
    2. Lo transcribe con Whisper
    3. Extrae entidades con BETO
    4. Guarda todo en PostgreSQL asociado al user_hash
    5. Devuelve el JSON con los materiales extraídos
    """
    if _use_case is None:
        raise HTTPException(status_code=500, detail="El motor de IA no está inicializado")

    # Validar extensión
    allowed_extensions = [".wav", ".m4a", ".mp3", ".ogg"]
    file_ext = os.path.splitext(audio.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Formato no soportado: {file_ext}. Usa: {allowed_extensions}")

    # Guardar audio en disco local (MVP) - En producción sería S3/R2
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_filename = f"{user_hash}_{uuid.uuid4().hex[:8]}{file_ext}"
    audio_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    try:
        # Ejecutar el caso de uso principal
        record = _use_case.execute(user_hash=user_hash, audio_path=audio_path)

        return {
            "status": "success",
            "data": {
                "id": record.id,
                "user_hash": record.user_hash,
                "audio_url": f"/uploads/{unique_filename}",
                "transcription": record.transcription,
                "extracted_data": record.extracted_data.model_dump(),
                "created_at": record.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")

@router.get("/user/{user_hash}", response_model=dict)
async def get_user_extractions(
    user_hash: str,
    _api_key: str = Depends(require_api_key)  # 🔒 Protegido con API Key
):
    """
    Devuelve el historial de todas las extracciones de un usuario.
    Así tu app Flutter puede mostrar los 5 (o N) audios que le pertenecen 
    al usuario y verificar que estén bien.
    
    REQUIERE el header X-Api-Key para autenticarse.
    """
    if _repository is None:
        raise HTTPException(status_code=500, detail="Repositorio no inicializado")

    records = _repository.get_by_user_hash(user_hash)
    
    return {
        "status": "success",
        "user_hash": user_hash,
        "total": len(records),
        "extractions": [
            {
                "id": r.id,
                "audio_url": r.audio_url,
                "transcription": r.transcription,
                "extracted_data": r.extracted_data.model_dump(),
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]
    }
