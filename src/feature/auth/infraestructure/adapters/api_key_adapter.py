from src.feature.auth.domain.auth_repository import IAuthService
from src.core.config import settings

class ApiKeyAuthAdapter(IAuthService):
    """
    Adaptador que valida el API Key contra la variable de entorno MICROSERVICE_API_KEY.
    Tu API principal debe enviar este key en cada petición para demostrar
    que es una fuente de confianza.
    """
    def __init__(self):
        self.valid_api_key = settings.MICROSERVICE_API_KEY

    def validate_api_key(self, api_key: str) -> bool:
        return api_key == self.valid_api_key
