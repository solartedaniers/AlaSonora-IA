"""Pruebo que la clave interna sea obligatoria y que las variables de entorno manden, sin leer el .env.
Lo ejecuto con: python -m app.test_config"""

import os
from unittest import mock

from pydantic import ValidationError

from app.config import Settings


def main() -> None:
    # Sin INTERNAL_API_KEY el motor no arranca: nunca queda expuesto sin autenticación.
    with mock.patch.dict(os.environ, {}, clear=True):
        try:
            Settings(_env_file=None)
        except ValidationError:
            pass
        else:
            raise AssertionError("Settings must require INTERNAL_API_KEY")

    overrides = {
        "INTERNAL_API_KEY": "key",
        "PHOTO_CLASSIFICATION_ENABLED": "false",
        "MAX_INFERENCE_WORKERS": "4",
        "AUDIO_HIGHPASS_CUTOFF_HZ": "250.5",
    }
    with mock.patch.dict(os.environ, overrides, clear=True):
        settings = Settings(_env_file=None)
    assert settings.internal_api_key == "key"
    assert settings.photo_classification_enabled is False
    assert settings.max_inference_workers == 4
    assert settings.audio_highpass_cutoff_hz == 250.5
    print("config self-check: OK")


if __name__ == "__main__":
    main()
