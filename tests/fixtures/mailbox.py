"""
Kutia postare e testeve: regjistrimi kërkon konfirmim me email (ADR 0016), prandaj çdo test që
ka nevojë për një përdorues të hyrë e regjistron, lexon lidhjen nga mesazhi i dërguar dhe e konfirmon.

Asnjë test nuk dërgon email të vërtetë: `OutboxMailer` mban mesazhet në kujtesë.
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from analyte.config import Settings
from analyte.mail import Message, OutboxMailer
from analyte.main import create_app
from analyte.orchestration.tasks import InlineRunner, Services

_TOKEN = re.compile(r"/confirm\?token=([A-Za-z0-9_\-]+)")


def client_for(settings: Settings, services: Services, runner=None) -> TestClient:
    """Aplikacion me kuti postare në kujtesë, e arritshme si `client.outbox`."""
    outbox = OutboxMailer()
    client = TestClient(create_app(settings, services, runner or InlineRunner(services), outbox))
    client.outbox = outbox  # type: ignore[attr-defined]
    return client


def token_in(message: Message) -> str:
    match = _TOKEN.search(message.body)
    assert match, f"mesazhi nuk ka lidhje konfirmimi: {message.subject!r}"
    return match.group(1)


def register_confirmed(client: TestClient, email: str, password: str) -> None:
    """Regjistron, merr lidhjen nga email-i i fundit për këtë adresë dhe e konfirmon."""
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 202, response.text
    sent = client.outbox.to(email.strip().lower())  # type: ignore[attr-defined]
    confirmed = client.post("/auth/confirm", json={"token": token_in(sent[-1])})
    assert confirmed.status_code == 204, confirmed.text
