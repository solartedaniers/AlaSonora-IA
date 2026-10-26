from fastapi import UploadFile

CHUNK_BYTES = 1024 * 1024


class UploadTooLargeError(Exception):
    """El archivo pasó el límite: dejé de leerlo apenas lo superó."""


class BoundedUploadReader:
    """Leo un archivo subido por trozos y corto en cuanto pasa max_bytes, sin cargarlo entero."""

    def __init__(self, max_bytes: int) -> None:
        self._max_bytes = max_bytes

    async def read(self, upload: UploadFile) -> bytes:
        if upload.size is not None and upload.size > self._max_bytes:
            raise UploadTooLargeError()
        chunks: list[bytes] = []
        total = 0
        while chunk := await upload.read(CHUNK_BYTES):
            total += len(chunk)
            if total > self._max_bytes:
                raise UploadTooLargeError()
            chunks.append(chunk)
        return b"".join(chunks)
