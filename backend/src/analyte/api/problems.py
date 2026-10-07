"""
Gabimet si "problem details" (RFC 7807).

"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import headers

MEDIA_TYPE = "application/problem+json"
log = logging.getLogger("analyte.api")


class Problem(Exception):
    def __init__(
        self,
        status: int,
        title: str,
        detail: str = "",
        kind: str = "about:blank",
        headers: dict[str, str] | None = None,
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.kind = kind
        self.headers = headers or {}


def _response(
    status: int,
    title: str,
    detail: str,
    kind: str,
    instance: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = {"type": kind, "title": title, "status": status, "instance": instance}
    if detail:
        body["detail"] = detail
    return JSONResponse(body, status_code=status, media_type=MEDIA_TYPE, headers=headers)


def install(app: FastAPI) -> None:
    @app.exception_handler(Problem)
    async def _problem(request: Request, error: Problem) -> JSONResponse:
        return _response(
            error.status, error.title, error.detail, error.kind, request.url.path, error.headers
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, error: StarletteHTTPException) -> JSONResponse:
        return _response(error.status_code, str(error.detail), "", "about:blank", request.url.path)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, error: RequestValidationError) -> JSONResponse:
        fields = ", ".join(
            ".".join(str(p) for p in e["loc"][1:]) or "trupi" for e in error.errors()
        )
        return _response(
            422, "Kërkesë e pavlefshme", f"fushat: {fields}", "about:blank", request.url.path
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, error: Exception) -> JSONResponse:
        log.error("gabim i papritur: %s", type(error).__name__)
        # Këtë përgjigje e nxjerr Starlette përtej middleware-it të kokave, prandaj i shtohen këtu.
        return _response(
            500,
            "Gabim i brendshëm",
            "",
            "about:blank",
            request.url.path,
            headers.for_path(request.url.path),
        )
