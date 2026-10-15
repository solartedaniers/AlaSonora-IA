import asyncio
import functools
import os
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, status
from fastapi.security import APIKeyHeader

from app.audio_quality import NoBirdSignalDetectedError, TooNoisyAudioError
from app.classifier import BirdNetClassifier
from app.config import settings
from app.schemas import ClassificationResponse, PhotoClassificationCandidate, PhotoClassificationResponse

api_key_header = APIKeyHeader(name="X-Internal-Api-Key")


def require_api_key(api_key: str = Depends(api_key_header)) -> None:
    if api_key != settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cargado una sola vez al iniciar: el modelo BirdNET pesa varios cientos
    # de MB y su carga es lenta, repetirla por request sería inaceptable.
    app.state.classifier = BirdNetClassifier()
    app.state.inference_pool = ThreadPoolExecutor(max_workers=settings.max_inference_workers)
    yield
    app.state.inference_pool.shutdown(wait=False)


app = FastAPI(title="AlaSonora AI Engine", lifespan=lifespan)


# Render revisa la ruta de salud con HEAD: sin aceptarlo respondía 405 y el servicio no quedaba sano al
# despertar. No carga nada pesado: el modelo ya se cargó al arrancar.
@app.api_route("/health", methods=["GET", "HEAD"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=ClassificationResponse, dependencies=[Depends(require_api_key)])
async def analyze(
    audio: UploadFile,
    min_confidence: float = Form(default=settings.default_min_confidence),
    max_results: int = Form(default=settings.default_max_results),
    recorded_at: datetime | None = Form(default=None),
    # Opcionales: solo deben venir cuando el backend tiene una ubicación GPS
    # real del dispositivo (ver BirdNetClassifier.classify).
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
) -> ClassificationResponse:
    suffix = os.path.splitext(audio.filename or "recording.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
        tmp_file.write(await audio.read())
        tmp_path = tmp_file.name

    try:
        loop = asyncio.get_running_loop()
        # El análisis de BirdNET es bloqueante/CPU-bound (TFLite); se despacha
        # a un ThreadPoolExecutor acotado para no congelar el event loop de
        # FastAPI mientras corre.
        candidates = await loop.run_in_executor(
            app.state.inference_pool,
            app.state.classifier.classify,
            tmp_path,
            recorded_at,
            min_confidence,
            max_results,
            latitude,
            longitude,
        )
    except TooNoisyAudioError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=settings.too_noisy_message) from exc
    except NoBirdSignalDetectedError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=settings.no_bird_signal_message) from exc
    finally:
        os.remove(tmp_path)

    return ClassificationResponse(candidates=candidates)


@app.post("/classify-photo", response_model=PhotoClassificationResponse, dependencies=[Depends(require_api_key)])
async def classify_photo(
    photo: UploadFile,
    min_confidence: float = Form(default=settings.default_photo_min_confidence),
    max_results: int = Form(default=settings.default_photo_max_results),
) -> PhotoClassificationResponse:
    if not settings.photo_classification_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=settings.photo_disabled_message)
    image_bytes = await photo.read()
    loop = asyncio.get_running_loop()
    candidates = await loop.run_in_executor(
        app.state.inference_pool, _classify_photo, image_bytes, min_confidence, max_results
    )
    return PhotoClassificationResponse(candidates=candidates)


# Carga perezosa: torch + transformers + EfficientNetB2 suman ~430 MB de RAM,
# así que solo se importan la primera vez que alguien usa /classify-photo
# (dentro del pool, para no congelar el event loop). El lock evita que dos
# peticiones simultáneas carguen el modelo dos veces.
_photo_classifier_lock = threading.Lock()


@functools.cache
def _load_photo_classifier():
    from app.photo_classifier import BirdPhotoClassifier

    return BirdPhotoClassifier(settings.photo_model_id)


def _classify_photo(image_bytes: bytes, min_confidence: float, max_results: int) -> list[PhotoClassificationCandidate]:
    from app.photo_classifier import NoBirdInPhotoError

    with _photo_classifier_lock:
        classifier = _load_photo_classifier()
    try:
        return classifier.classify(image_bytes, min_confidence, max_results)
    except NoBirdInPhotoError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=settings.no_bird_in_photo_message) from exc
