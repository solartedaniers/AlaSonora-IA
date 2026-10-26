import numpy as np
from scipy.signal import butter, sosfiltfilt


class AudioPreprocessor:
    """Quito el retumbo grave (viento, manejo del micrófono) y normalizo el volumen antes de BirdNET.
    El ruido que queda lo juzga después AudioQualityAnalyzer."""

    def __init__(self, highpass_cutoff_hz: float = 300.0, filter_order: int = 4) -> None:
        self._highpass_cutoff_hz = highpass_cutoff_hz
        self._filter_order = filter_order

    def clean(self, samples: np.ndarray, sample_rate: int) -> np.ndarray:
        filtered = self._apply_highpass(samples, sample_rate)
        return self._normalize(filtered)

    def _apply_highpass(self, samples: np.ndarray, sample_rate: int) -> np.ndarray:
        nyquist = sample_rate / 2
        # Uso sosfiltfilt (ida y vuelta) para no desfasar la señal.
        sos = butter(self._filter_order, self._highpass_cutoff_hz / nyquist, btype="highpass", output="sos")
        return sosfiltfilt(sos, samples)

    def _normalize(self, samples: np.ndarray) -> np.ndarray:
        peak = np.max(np.abs(samples))
        if peak == 0:
            return samples
        return samples / peak
