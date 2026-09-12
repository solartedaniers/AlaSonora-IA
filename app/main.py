from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader

from app.classifier import BirdNetClassifier
from app.config import settings

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

