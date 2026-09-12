class TooNoisyAudioError(Exception):
    """La grabación tiene demasiado ruido estático/de fondo para analizarla."""


class NoBirdSignalDetectedError(Exception):
    """Hay sonido en la grabación, pero no en el rango espectral típico del canto de aves."""

