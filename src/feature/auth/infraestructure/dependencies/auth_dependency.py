from fastapi import Header, HTTPException, Depends

from src.feature.auth.infraestructure.adapters.api_key_adapter import ApiKeyAuthAdapter
from src.feature.auth.application.use_cases import ValidateApiKeyUseCase

# Instancia única del servicio de auth
_auth_adapter = ApiKeyAuthAdapter()
_validate_use_case = ValidateApiKeyUseCase(auth_service=_auth_adapter)

async def require_api_key(x_api_key: str = Header(..., description="API Key del microservicio")):
    """
    Dependencia de FastAPI: se inyecta en cualquier endpoint que necesite autenticación.
    
    Tu API principal debe enviar el header:
        X-Api-Key: visionprice-secret-key-2024
    
    Si el key no es válido, devuelve 401 Unauthorized.
    """
    if not _validate_use_case.execute(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="API Key inválido. Este microservicio solo acepta peticiones de la API principal."
        )
    return x_api_key
