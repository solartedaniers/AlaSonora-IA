"""Self-check de la clave interna: /analyze y /classify-photo solo responden al backend, que envía
X-Internal-Api-Key. No arranca el lifespan, así que no carga ningún modelo.
Ejecutar con: python -m app.test_auth"""

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

PROTECTED_PATHS = ("/analyze", "/classify-photo")


def main() -> None:
    client = TestClient(app)
    for path in PROTECTED_PATHS:
        missing = client.post(path)
        assert missing.status_code == 401, (path, missing.status_code)

        wrong = client.post(path, headers={"X-Internal-Api-Key": settings.internal_api_key + "-wrong"})
        assert wrong.status_code == 401, (path, wrong.status_code)
        assert wrong.json()["detail"] == "Invalid API key"

    # Con la clave correcta pasa la autenticación y lo siguiente que falla es la validación del cuerpo.
    no_audio = client.post("/analyze", headers={"X-Internal-Api-Key": settings.internal_api_key})
    assert no_audio.status_code == 422, no_audio.status_code
    print("auth self-check: OK")


if __name__ == "__main__":
    main()
