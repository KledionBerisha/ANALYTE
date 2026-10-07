"""
Bota e përbashkët e testeve të llogarisë (ADR 0018): rivendosja, hapi i dytë, rindërgimi.

Çdo test merr një aplikacion me SQLite në dosje të përkohshme dhe kuti postare në kujtesë. Pritja midis provave të
dërgimit është zero, që testet të mos presin.
"""

from __future__ import annotations

import time
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from analyte import twofactor
from analyte.config import Settings
from analyte.generation.templates import TemplateGenerator
from analyte.main import create_app
from analyte.orchestration.tasks import InlineRunner, Services
from analyte.persistence.database import create_schema, make_engine, make_session_factory
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import AuditEventRow, UserRow
from tests.fixtures.mailbox import client_for, register_confirmed

PASSWORD = "fjalekalim-testi-i-gjate"
NEW_PASSWORD = "fjalekalim-i-ri-i-gjate"
EMAIL = "viktima@shembull.al"
SECRET = "t" * 48


class World:
    def __init__(self, tmp: Path, mailer=None, **overrides) -> None:
        overrides.setdefault("mail_retry_backoff_seconds", 0)
        # `database_url` jepet vetëm nga testet mbi PostgreSQL, ku skema është ndërtuar tashmë nga migrimet.
        database_url = overrides.pop("database_url", None)
        self.settings = Settings(
            database_url=database_url or f"sqlite:///{tmp / 'analyte.db'}",
            jwt_secret=SECRET,
            storage_key=Fernet.generate_key().decode(),
            storage_dir=tmp / "storage",
            job_runner="inline",
            ocr=False,
            **overrides,
        )
        engine = make_engine(self.settings.database_url)
        if database_url is None:
            create_schema(engine)
        self.services = Services(
            sessions=make_session_factory(engine),
            store=EncryptedStore(self.settings.storage_dir, self.settings.storage_key),
            generator=TemplateGenerator(),
        )
        if mailer is None:
            self.client = client_for(self.settings, self.services)
            self.outbox = self.client.outbox
        else:
            self.client = TestClient(
                create_app(self.settings, self.services, InlineRunner(self.services), mailer)
            )
            self.outbox = mailer
        self.app = self.client.app

    # veprime
    def register(self, email: str = EMAIL, password: str = PASSWORD, ip: str | None = None):
        return self.client.post(
            "/auth/register", json={"email": email, "password": password}, headers=_ip(ip)
        )

    def confirmed(self, email: str = EMAIL, password: str = PASSWORD) -> None:
        register_confirmed(self.client, email, password)

    def login(self, email: str = EMAIL, password: str = PASSWORD, ip: str | None = None):
        return self.client.post(
            "/auth/login", json={"email": email, "password": password}, headers=_ip(ip)
        )

    def tokens(self, email: str = EMAIL, password: str = PASSWORD) -> dict:
        response = self.login(email, password)
        assert response.status_code == 200 and "access_token" in response.json(), response.text
        return response.json()

    def forgot(self, email: str = EMAIL, ip: str | None = None):
        return self.client.post("/auth/forgot-password", json={"email": email}, headers=_ip(ip))

    def reset(self, token: str, password: str = NEW_PASSWORD, ip: str | None = None):
        return self.client.post(
            "/auth/reset-password", json={"token": token, "password": password}, headers=_ip(ip)
        )

    def me(self, access: str):
        return self.client.get("/auth/me", headers=bearer(access))

    def authed(self, access: str, method: str, path: str, **kwargs):
        return self.client.request(method, path, headers=bearer(access), **kwargs)

    def verify(self, challenge: str, code: str, ip: str | None = None):
        return self.client.post(
            "/auth/login/verify", json={"challenge": challenge, "code": code}, headers=_ip(ip)
        )

    # hapi i dytë
    def enable_two_factor(
        self, email: str = EMAIL, password: str = PASSWORD
    ) -> tuple[str, list[str], dict]:
        """Regjistron hapin e dytë; kthen sekretin, kodet e rimëkëmbjes dhe tokenët e seancës që e aktivizoi."""
        tokens = self.tokens(email, password)
        enrolled = self.authed(tokens["access_token"], "POST", "/auth/2fa/enroll")
        assert enrolled.status_code == 200, enrolled.text
        secret = enrolled.json()["secret"]
        confirmed = self.authed(
            tokens["access_token"], "POST", "/auth/2fa/confirm", json={"code": code_for(secret)}
        )
        assert confirmed.status_code == 200, confirmed.text
        return secret, confirmed.json()["recovery_codes"], tokens

    # baza
    def db(self):
        return self.services.sessions()

    def user(self, email: str = EMAIL) -> UserRow:
        with self.db() as db:
            user = db.scalars(select(UserRow).where(UserRow.email == email)).one()
            db.expunge(user)
            return user

    def audit(self, event_type: str) -> list[AuditEventRow]:
        with self.db() as db:
            return list(
                db.scalars(select(AuditEventRow).where(AuditEventRow.event_type == event_type))
            )


def bearer(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


def _ip(ip: str | None) -> dict[str, str]:
    return {"X-Forwarded-For": ip} if ip else {}


def code_for(secret: str, offset: int = 0) -> str:
    """Kodi TOTP i hapit të tanishëm (ose një hapi tjetër brenda dritares: -1, 0, +1)."""
    return twofactor.code_at(secret, twofactor.step_of(time.time()) + offset)


def wrong_code(secret: str) -> str:
    """Një kod gjashtëshifror që nuk vlen për asnjë hap të dritares."""
    valid = {code_for(secret, offset) for offset in (-2, -1, 0, 1, 2)}
    return next(c for c in ("000000", "111111", "222222", "333333") if c not in valid)
