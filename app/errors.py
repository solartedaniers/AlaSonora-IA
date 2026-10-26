from enum import StrEnum

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErrorCode(StrEnum):
    """Códigos estables en inglés: el backend los traduce a su ApiErrorCode y el frontend muestra el texto."""

    AUDIO_TOO_LARGE = "AUDIO_TOO_LARGE"
    AUDIO_UNSUPPORTED = "AUDIO_UNSUPPORTED"
    TOO_NOISY = "TOO_NOISY"
    NO_BIRD_SIGNAL = "NO_BIRD_SIGNAL"
    PHOTO_TOO_LARGE = "PHOTO_TOO_LARGE"
    PHOTO_UNSUPPORTED = "PHOTO_UNSUPPORTED"
    NO_BIRD_IN_PHOTO = "NO_BIRD_IN_PHOTO"
    PHOTO_DISABLED = "PHOTO_DISABLED"


# Solo para leer en logs o con curl: el texto para el usuario vive en el i18n del frontend.
DETAILS = {
    ErrorCode.AUDIO_TOO_LARGE: "The audio file exceeds the maximum allowed size",
    ErrorCode.AUDIO_UNSUPPORTED: "Unsupported audio format; use WAV, FLAC or MP3",
    ErrorCode.TOO_NOISY: "Too much background noise in the recording",
    ErrorCode.NO_BIRD_SIGNAL: "No bird sound was detected in the recording",
    ErrorCode.PHOTO_TOO_LARGE: "The photo exceeds the maximum allowed size",
    ErrorCode.PHOTO_UNSUPPORTED: "Unsupported photo format; use JPEG, PNG or WebP",
    ErrorCode.NO_BIRD_IN_PHOTO: "No bird could be identified in the photo",
    ErrorCode.PHOTO_DISABLED: "Photo identification is disabled in this deployment",
}


class EngineError(Exception):
    """Error del motor con su código estable y un detalle corto en inglés."""

    def __init__(self, status_code: int, code: ErrorCode) -> None:
        super().__init__(DETAILS[code])
        self.status_code = status_code
        self.code = code
        self.detail = DETAILS[code]


async def _engine_error_response(_: Request, error: EngineError) -> JSONResponse:
    # Conservo "detail" para que un backend anterior siga leyendo el error como hoy.
    return JSONResponse(status_code=error.status_code, content={"code": error.code, "detail": error.detail})


def register_engine_errors(app: FastAPI) -> None:
    app.add_exception_handler(EngineError, _engine_error_response)
