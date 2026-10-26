from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class EngineError(Exception):
    """Error con un código estable en inglés que el backend traduce a su ApiErrorCode."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


async def _engine_error_response(_: Request, error: EngineError) -> JSONResponse:
    # Conservo "detail" para que un backend anterior siga leyendo el error como hoy.
    return JSONResponse(status_code=error.status_code, content={"code": error.code, "detail": error.detail})


def register_engine_errors(app: FastAPI) -> None:
    app.add_exception_handler(EngineError, _engine_error_response)
