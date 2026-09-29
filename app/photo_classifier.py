from transformers import AutoImageProcessor, AutoModelForImageClassification


class NoBirdInPhotoError(Exception):
    """Raised when even the top prediction falls below the confidence floor."""


class BirdPhotoClassifier:
    """Wraps a Hugging Face image-classification model (EfficientNetB2 fine-tuned
    on 525 bird species), fully independent from BirdNetClassifier — a different
    model, a different input modality (photo, not audio), loaded once here for
    the same reason: reloading per request would be wasteful.
    """

    def __init__(self, model_id: str) -> None:
        self._processor = AutoImageProcessor.from_pretrained(model_id)
        self._model = AutoModelForImageClassification.from_pretrained(model_id)
        self._model.eval()
