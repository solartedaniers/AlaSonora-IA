"""Self-check de los límites de subida: corto el audio o la foto que pasa el tope (413) y rechazo el
formato que no reconozco por su firma (415), siempre antes de clasificar.
Ejecutar con: python -m app.test_upload_limits"""

import asyncio
import io
from concurrent.futures import ThreadPoolExecutor

from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.bounded_upload import CHUNK_BYTES, BoundedUploadReader, UploadTooLargeError
from app.config import settings
from app.main import app

AUTH = {"X-Internal-Api-Key": settings.internal_api_key}
WAV = b"RIFF\x00\x00\x00\x00WAVEdata"
FLAC = b"fLaC\x00\x00\x00\x22data"
MP3_ID3 = b"ID3\x04\x00\x00\x00\x00data"
MP3_FRAME = b"\xff\xfb\x90\x64data"


class CountingClassifier:
    def __init__(self) -> None:
        self.calls = 0

    def classify(self, *args):
        self.calls += 1
        return []


def _post_audio(client: TestClient, content: bytes):
    return client.post("/analyze", headers=AUTH, files={"audio": ("recording.wav", content, "audio/wav")})


def _check_audio() -> None:
    classifier = CountingClassifier()
    app.state.classifier = classifier
    client = TestClient(app)

    # El backend manda todo como recording.wav: acepto WAV, FLAC y MP3 por su firma.
    for content in (WAV, FLAC, MP3_ID3, MP3_FRAME):
        assert _post_audio(client, content).status_code == 200, content
    assert classifier.calls == 4

    response = _post_audio(client, b"%PDF-1.7 not audio")
    assert response.status_code == 415, response.status_code
    assert response.json()["code"] == "AUDIO_UNSUPPORTED"

    original = settings.max_audio_bytes
    settings.max_audio_bytes = len(WAV) - 1
    try:
        response = _post_audio(client, WAV)
    finally:
        settings.max_audio_bytes = original
    assert response.status_code == 413, response.status_code
    assert response.json()["code"] == "AUDIO_TOO_LARGE"
    assert "detail" in response.json()
    assert classifier.calls == 4


def _check_photo() -> None:
    client = TestClient(app)
    original = (settings.photo_classification_enabled, settings.max_photo_bytes)
    settings.photo_classification_enabled = True
    try:
        response = client.post("/classify-photo", headers=AUTH, files={"photo": ("bird.jpg", b"not-an-image", "image/jpeg")})
        assert response.status_code == 415, response.status_code
        assert response.json()["code"] == "PHOTO_UNSUPPORTED"

        settings.max_photo_bytes = 4
        response = client.post("/classify-photo", headers=AUTH, files={"photo": ("bird.jpg", b"\xff\xd8\xff\xe0jpeg", "image/jpeg")})
        assert response.status_code == 413, response.status_code
        assert response.json()["code"] == "PHOTO_TOO_LARGE"
    finally:
        settings.photo_classification_enabled, settings.max_photo_bytes = original


def _check_reader_stops_early() -> None:
    # Sin tamaño declarado leo por trozos y paro en cuanto paso el tope, sin terminar el archivo.
    stream = io.BytesIO(b"x" * (CHUNK_BYTES * 5))
    upload = UploadFile(stream)
    try:
        asyncio.run(BoundedUploadReader(CHUNK_BYTES + 1).read(upload))
        raise AssertionError("expected UploadTooLargeError")
    except UploadTooLargeError:
        pass
    assert stream.tell() <= CHUNK_BYTES * 2, stream.tell()

    exact = UploadFile(io.BytesIO(b"y" * 10))
    assert asyncio.run(BoundedUploadReader(10).read(exact)) == b"y" * 10


def main() -> None:
    app.state.inference_pool = ThreadPoolExecutor(max_workers=1)
    try:
        _check_audio()
        _check_photo()
        _check_reader_stops_early()
    finally:
        app.state.inference_pool.shutdown()
        del app.state.inference_pool, app.state.classifier
    print("upload limits self-check: OK")


if __name__ == "__main__":
    main()
