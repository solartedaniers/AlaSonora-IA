"""Pruebo AudioPreprocessor con señales sintéticas.
Lo ejecuto con: python -m app.test_audio_preprocessing"""

import numpy as np

from app.audio_preprocessing import AudioPreprocessor

SAMPLE_RATE = 22050
TIME = np.linspace(0, 1, SAMPLE_RATE, endpoint=False)


def _check_normalization(preprocessor: AudioPreprocessor) -> None:
    # Una grabación débil queda con pico 1 para no caer bajo el umbral de BirdNET.
    quiet_song = 0.05 * np.sin(2 * np.pi * 3000 * TIME)
    assert np.isclose(np.max(np.abs(preprocessor.clean(quiet_song, SAMPLE_RATE))), 1.0)

    # Con silencio no divido entre cero: sale igual que entró.
    silence = np.zeros(SAMPLE_RATE)
    assert np.array_equal(preprocessor.clean(silence, SAMPLE_RATE), silence)


def _component(samples: np.ndarray, frequency_hz: float) -> float:
    spectrum = np.abs(np.fft.rfft(samples))
    return float(spectrum[int(round(frequency_hz * len(samples) / SAMPLE_RATE))])


def _check_highpass(preprocessor: AudioPreprocessor) -> None:
    # El retumbo de 60 Hz (viento, manejo del micrófono) casi desaparece; el canto de 3 kHz se conserva.
    rumble_and_song = np.sin(2 * np.pi * 60 * TIME) + np.sin(2 * np.pi * 3000 * TIME)
    cleaned = preprocessor.clean(rumble_and_song, SAMPLE_RATE)
    assert _component(cleaned, 60) < 0.01 * _component(cleaned, 3000)


def main() -> None:
    preprocessor = AudioPreprocessor()
    _check_normalization(preprocessor)
    _check_highpass(preprocessor)
    print("audio_preprocessing self-check: OK")


if __name__ == "__main__":
    main()
