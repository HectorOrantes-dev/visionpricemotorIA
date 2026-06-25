from abc import ABC, abstractmethod

class IAuthService(ABC):
    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        """
        Valida que la petición viene de una fuente autorizada (tu API principal).
        NO valida al usuario final — eso lo hace tu API principal.
        Este microservicio solo confía en peticiones que traigan el API Key correcto.
        """
        pass
