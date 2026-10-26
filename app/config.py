from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Leo toda la configuración de variables de entorno (o .env), nunca de valores quemados."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    internal_api_key: str
    default_min_confidence: float = 0.1
    default_max_results: int = 3
    max_inference_workers: int = 2
    # Mismo tope que audio.upload.max-bytes del backend (10 MB); la foto usa el mismo.
    max_audio_bytes: int = 10485760
    max_photo_bytes: int = 10485760

    # Dejo configurables el filtro y los umbrales de calidad para recalibrarlos sin tocar código.
    audio_highpass_cutoff_hz: float = 300.0
    audio_noise_flatness_threshold: float = 0.3
    audio_bird_band_energy_ratio_threshold: float = 0.15

    # Fotos: por defecto true; en producción (Render, 512 MB) va en false porque torch y transformers no caben.
    photo_classification_enabled: bool = True
    photo_model_id: str = "dennisjooo/Birds-Classifier-EfficientNetB2"
    default_photo_min_confidence: float = 0.3
    default_photo_max_results: int = 3


settings = Settings()
