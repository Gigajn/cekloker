"""Format error JSON konsisten + jangan bocorkan stack trace (ARCH §8).

Semua error API berbentuk:
    {"error": {"code": "<kode>", "message": "<pesan>", "details": {...}?}}

- 404 resource -> code "not_found"
- 422 validasi Pydantic -> code "validation_error" + details per-field
- 500 tak terduga -> code "internal_error", pesan generik saja.
  Traceback HANYA ditulis ke log server, tidak pernah ke respons.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("cekloker.api")


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(message: str = "Data tidak ditemukan.") -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "not_found", message)


def _error_body(code: str, message: str, details: object = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("validation_error", "Input tidak valid.", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Termasuk 401 dari auth (bukan ApiError): samakan bentuknya.
        code = {401: "unauthorized", 403: "forbidden", 404: "not_found"}.get(
            exc.status_code, "http_error"
        )
        detail = exc.detail if isinstance(exc.detail, str) else "Terjadi kesalahan."
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, detail),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Traceback hanya ke log server — TIDAK PERNAH ke respons publik.
        log.exception("kesalahan internal tak terduga di %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                "internal_error", "Terjadi kesalahan internal. Coba lagi nanti."
            ),
        )
