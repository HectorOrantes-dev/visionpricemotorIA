import httpx

from src.feature.extraction.domain.repositories import IMlCallbackNotifier


class HttpCallbackAdapter(IMlCallbackNotifier):
    """
    Notifica al back-end principal el resultado del procesamiento asíncrono.
    Hace POST a la URL configurada enviando el header X-Api-Key.
    """

    def __init__(self, callback_url: str, api_key: str, timeout: float = 15.0):
        self.callback_url = callback_url
        self.api_key = api_key
        self.timeout = timeout

    def notify(self, payload: dict) -> None:
        if not self.callback_url:
            print("⚠️ ML_CALLBACK_URL no configurada; se omite el callback.")
            return

        try:
            response = httpx.post(
                self.callback_url,
                json=payload,
                headers={"X-Api-Key": self.api_key},
                timeout=self.timeout,
            )
            response.raise_for_status()
            print(f"✅ Callback enviado ({response.status_code}) para grabacion {payload.get('grabacion_id')}")
        except Exception as e:
            # No relanzamos: el callback es best-effort; lo registramos para diagnóstico.
            print(f"❌ Error enviando callback para grabacion {payload.get('grabacion_id')}: {e}")
