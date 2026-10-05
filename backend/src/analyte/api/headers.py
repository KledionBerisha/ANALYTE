"""
Kokat bazë të sigurisë në çdo përgjigje të API-së (ADR 0018).

  - `Referrer-Policy: no-referrer` — adresat e API-së nuk duhet të rrjedhin te faqe të tjera si `Referer`;
  - `X-Content-Type-Options: nosniff` — shfletuesi nuk e hamendëson llojin e përmbajtjes (figurat e faqeve,
    JSON-i i gabimeve);
  - `X-Frame-Options: DENY` — përgjigjet e API-së nuk vendosen në kornizë;
  - `Cache-Control: no-store` për `/auth/*` — tokenët, sfidat dhe kodet e rimëkëmbjes nuk ruhen në cache të
    shfletuesit ose të një ndërmjetësi.

Middleware është ASGI i pastër, jo `BaseHTTPMiddleware`: nuk e lexon trupin, prandaj nuk ndërhyn te figurat e
faqeve dhe te detyrat në sfond.

Gabimet e papritura (500) i nxjerr middleware-i më i jashtëm i Starlette-it, përtej këtij; prandaj
`problems._unexpected` i shton vetë me `for_path`.
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
