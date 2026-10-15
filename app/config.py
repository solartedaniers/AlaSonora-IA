from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toda la configuración sale de variables de entorno (o .env), nunca de valores quemados, igual que en el backend."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    internal_api_key: str
    default_min_confidence: float = 0.1
    default_max_results: int = 3
    max_inference_workers: int = 2

    # Preprocesamiento y control de calidad de audio (ver AudioPreprocessor
    # y AudioQualityAnalyzer) — configurables para poder recalibrar sin tocar código.
    audio_highpass_cutoff_hz: float = 300.0
    audio_noise_flatness_threshold: float = 0.3
    audio_bird_band_energy_ratio_threshold: float = 0.15

    # Identificación por foto (modelo separado, sin relación con BirdNET).
    # En false, /classify-photo responde 503 sin cargar el modelo: torch +
    # transformers suman ~430 MB y no caben en instancias de 512 MB.
    photo_classification_enabled: bool = True
    photo_model_id: str = "dennisjooo/Birds-Classifier-EfficientNetB2"
    default_photo_min_confidence: float = 0.3
    default_photo_max_results: int = 3

    # Mensajes que el backend reenvía tal cual al usuario final en el "detail" de la respuesta.
    too_noisy_message: str = "Demasiada interferencia de ruido, por favor grabe de nuevo o cargue un audio más limpio"
    no_bird_signal_message: str = "No se detecta sonido de aves en la grabación, por favor intente nuevamente"
    no_bird_in_photo_message: str = "No se pudo identificar un ave en esta foto, por favor intente con otra imagen"
    photo_disabled_message: str = "La identificación por foto no está disponible en este despliegue"


settings = Settings()
