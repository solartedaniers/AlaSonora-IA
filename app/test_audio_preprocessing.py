"""Self-check de AudioPreprocessor con señales sintéticas.
Ejecutar con: python -m app.test_audio_preprocessing"""

import numpy as np

from app.audio_preprocessing import AudioPreprocessor

SAMPLE_RATE = 22050
TIME = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)


def _check_normalization(preprocessor: AudioPreprocessor) -> None:
    # Una grabación débil queda con pico 1 para no caer bajo el umbral de BirdNET.
    quiet_song = 0.05 * np.sin(2 * np.pi * 3000 * TIME)
    assert np.isclose(np.max(np.abs(preprocessor.clean(quiet_song, SAMPLE_RATE))), 1.0)

    # El silencio no se divide entre cero: sale igual que entró.
    silence = np.zeros(SAMPLE_RATE)
    assert np.array_equal(preprocessor.clean(silence, SAMPLE_RATE), silence)


def main() -> None:
    preprocessor = AudioPreprocessor()
    _check_normalization(preprocessor)
    print("audio_preprocessing self-check: OK")


if __name__ == "__main__":
    main()
