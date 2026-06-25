from src.feature.auth.domain.auth_repository import IAuthService

class ValidateApiKeyUseCase:
    """
    Caso de uso: Validar que la petición viene de tu API principal.
    Si el API Key es incorrecto, rechaza la petición.
    """
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, api_key: str) -> bool:
        return self.auth_service.validate_api_key(api_key)
