from pydantic import BaseModel

class AuthenticatedRequest(BaseModel):
    """
    Representa una petición ya validada que viene de tu API principal.
    Contiene el user_hash del usuario móvil que hizo la grabación.
    """
    user_hash: str
    source: str = "api_principal"  # Origen de la petición
