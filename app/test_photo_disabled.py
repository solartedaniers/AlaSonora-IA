"""Self-check de PHOTO_CLASSIFICATION_ENABLED=false: /classify-photo responde 503 con su mensaje
sin importar torch ni transformers (así funciona el despliegue de 512 MB).
Ejecutar con: python -m app.test_photo_disabled"""

import sys

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def main() -> None:
    client = TestClient(app)
    original = settings.photo_classification_enabled
    settings.photo_classification_enabled = False
    try:
        response = client.post(
            "/classify-photo",
            headers={"X-Internal-Api-Key": settings.internal_api_key},
            files={"photo": ("bird.jpg", b"not-an-image", "image/jpeg")},
        )
    finally:
        settings.photo_classification_enabled = original

    assert response.status_code == 503, response.status_code
    assert response.json()["code"] == "PHOTO_DISABLED"
    # Con la bandera apagada nunca se carga el modelo de fotos.
    assert "app.photo_classifier" not in sys.modules
    print("photo disabled self-check: OK")


if __name__ == "__main__":
    main()
