"""
Kokat bazë të sigurisë në çdo përgjigje të API-së (ADR 0018).

"""

from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

BASE = {
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


def for_path(path: str) -> dict[str, str]:
    headers = dict(BASE)
    if path == "/auth" or path.startswith("/auth/"):
        headers["Cache-Control"] = "no-store"
    return headers


class SecurityHeaders:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        extra = for_path(scope["path"])

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for key, value in extra.items():
                    headers[key] = value
            await send(message)

        await self.app(scope, receive, send_with_headers)
