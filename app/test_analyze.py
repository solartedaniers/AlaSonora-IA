"""Self-check de /analyze con un clasificador falso en app.state (sin cargar BirdNET): reenvía los
parámetros del formulario, devuelve los candidatos y borra siempre el audio temporal.
Ejecutar con: python -m app.test_analyze"""

import os
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import ClassificationCandidate

AUTH = {"X-Internal-Api-Key": settings.internal_api_key}
AUDIO = {"audio": ("song.wav", b"RIFF-fake-audio", "audio/wav")}


class FakeClassifier:
    """Registra la llamada y responde lo que le indico, o lanza el error indicado."""

    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result or []
        self.error = error
        self.calls = []

    def classify(self, audio_path, recorded_at, min_confidence, max_results, latitude, longitude):
        self.calls.append((audio_path, min_confidence, max_results, latitude, longitude))
        assert os.path.exists(audio_path)
        if self.error:
            raise self.error
        return self.result


def _post(classifier: FakeClassifier, form: dict | None = None):
    app.state.classifier = classifier
    return TestClient(app).post("/analyze", headers=AUTH, files=AUDIO, data=form or {})


def _check_success() -> None:
    owl = ClassificationCandidate(scientific_name="Bubo virginianus", common_name="Great Horned Owl", confidence=0.7)
    classifier = FakeClassifier(result=[owl])
    response = _post(classifier, {"min_confidence": "0.25", "max_results": "2", "latitude": "4.6", "longitude": "-74.1"})

    assert response.status_code == 200, response.text
    assert response.json() == {"candidates": [owl.model_dump()]}
    audio_path, min_confidence, max_results, latitude, longitude = classifier.calls[0]
    assert (min_confidence, max_results, latitude, longitude) == (0.25, 2, 4.6, -74.1)
    assert audio_path.endswith(".wav") and not os.path.exists(audio_path)

    # Sin formulario se usan los valores por defecto de la configuración y no se envía ubicación.
    classifier = FakeClassifier()
    _post(classifier)
    assert classifier.calls[0][1:] == (settings.default_min_confidence, settings.default_max_results, None, None)


def main() -> None:
    app.state.inference_pool = ThreadPoolExecutor(max_workers=1)
    try:
        _check_success()
    finally:
        app.state.inference_pool.shutdown()
        del app.state.inference_pool, app.state.classifier
    print("analyze self-check: OK")


if __name__ == "__main__":
    main()
