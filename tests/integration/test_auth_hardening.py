"""
Kufizimi i hyrjeve dhe seancat e revokueshme (ADR 0014).

Dy grupe pohimesh:

  - **Kufizimi.** Çdo kovë ndalon atë që duhet të ndalojë dhe jo më shumë;
    një llogari nuk mbyllet nga një IP tjetër; email-i i panjohur dhe i
    njohur kufizohen njësoj; asnjë email dhe asnjë IP nuk ruhet si tekst,
    as në tabelë as në auditim.
  - **Seancat.** Tokeni i rifreskimit vlen një herë; ripërdorimi revokon
    gjithë seancën, edhe tokenin e aksesit; dalja revokon menjëherë; një
    token i lëshuar para ADR 0014 nuk pranohet.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from starlette.requests import Request

from analyte.api.throttle import client_ip, network_of
from tests.fixtures.mailbox import client_for, register_confirmed
from analyte.config import Settings
from analyte.generation.templates import TemplateGenerator
from analyte.main import create_app
from analyte.orchestration.tasks import InlineRunner, Services
from analyte.persistence.database import create_schema, make_engine, make_session_factory
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import (
    AuditEventRow,
    AuthSessionRow,
    LoginFailureRow,
    RefreshTokenRow,
    UserRow,
)

PASSWORD = "fjalekalim-testi-i-gjate"
WRONG = "fjalekalim-i-gabuar-xyz"


class World:
    def __init__(self, tmp: Path, **overrides) -> None:
        self.settings = Settings(
            database_url=f"sqlite:///{tmp / 'analyte.db'}",
            jwt_secret="t" * 48,
            storage_key=Fernet.generate_key().decode(),
            storage_dir=tmp / "storage",
            job_runner="inline",
            ocr=False,
            **overrides,
        )
        engine = make_engine(self.settings.database_url)
        create_schema(engine)
        self.services = Services(
            sessions=make_session_factory(engine),
            store=EncryptedStore(self.settings.storage_dir, self.settings.storage_key),
            generator=TemplateGenerator(),
        )
        self.client = client_for(self.settings, self.services)
        self.outbox = self.client.outbox

    def register(self, email: str) -> None:
        register_confirmed(self.client, email, PASSWORD)

    def login(self, email: str, password: str = PASSWORD, ip: str | None = None):
        headers = {"X-Forwarded-For": ip} if ip else {}
        return self.client.post(
            "/auth/login", json={"email": email, "password": password}, headers=headers
        )

    def tokens(self, email: str) -> dict[str, str]:
        response = self.login(email)
        assert response.status_code == 200, response.text
        return response.json()

    def refresh(self, token: str):
        return self.client.post("/auth/refresh", json={"refresh_token": token})

    def me(self, access: str):
        return self.client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})

    def db(self):
        return self.services.sessions()

    def audit(self, event_type: str) -> list[AuditEventRow]:
        with self.db() as db:
            return list(db.scalars(select(AuditEventRow).where(AuditEventRow.event_type == event_type)))


@pytest.fixture
def world(tmp_path):
    w = World(tmp_path)
    w.register("viktima@shembull.al")
    return w


def _fail(world: World, email: str, times: int, ip: str | None = None) -> None:
    for _ in range(times):
        assert world.login(email, WRONG, ip).status_code == 401


# --------------------------------------------------------------------
# Kufizimi i hyrjeve
# --------------------------------------------------------------------


def test_the_sixth_failed_login_is_throttled(world):
    _fail(world, "viktima@shembull.al", 5)
    blocked = world.login("viktima@shembull.al", WRONG)
    assert blocked.status_code == 429
    assert blocked.headers["content-type"].startswith("application/problem+json")
    assert 1 <= int(blocked.headers["retry-after"]) <= 15 * 60


def test_the_right_password_is_refused_while_throttled(world):
    _fail(world, "viktima@shembull.al", 5)
    assert world.login("viktima@shembull.al", PASSWORD).status_code == 429


def test_known_and_unknown_emails_are_throttled_identically(world):
    _fail(world, "viktima@shembull.al", 5)
    _fail(world, "askush@shembull.al", 5)
    known = world.login("viktima@shembull.al", WRONG)
    unknown = world.login("askush@shembull.al", WRONG)
    assert known.status_code == unknown.status_code == 429
    assert known.json()["title"] == unknown.json()["title"]
    assert known.json()["detail"] == unknown.json()["detail"]


def test_a_throttled_request_does_not_extend_the_lock(world):
    _fail(world, "viktima@shembull.al", 5)
    for _ in range(3):
        assert world.login("viktima@shembull.al", WRONG).status_code == 429
    with world.db() as db:
        assert len(db.scalars(select(LoginFailureRow)).all()) == 5


def test_an_attacker_elsewhere_cannot_lock_the_victim_out(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1)
    w.register("viktima@shembull.al")
    _fail(w, "viktima@shembull.al", 5, ip="203.0.113.7")
    assert w.login("viktima@shembull.al", WRONG, ip="203.0.113.7").status_code == 429
    assert w.login("viktima@shembull.al", PASSWORD, ip="198.51.100.2").status_code == 200


def test_one_address_cannot_spray_many_accounts(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1, login_max_failures_ip=6)
    for i in range(6):
        assert w.login(f"nje{i}@shembull.al", WRONG, ip="203.0.113.7").status_code == 401
    assert w.login("tjeter@shembull.al", WRONG, ip="203.0.113.7").status_code == 429
    assert w.login("tjeter@shembull.al", WRONG, ip="198.51.100.2").status_code == 401


def test_many_addresses_cannot_share_out_guesses_at_one_account(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1, login_max_failures_email=6)
    w.register("viktima@shembull.al")
    for i in range(6):
        assert w.login("viktima@shembull.al", WRONG, ip=f"203.0.113.{i}").status_code == 401
    assert w.login("viktima@shembull.al", WRONG, ip="198.51.100.99").status_code == 429


def test_a_successful_login_clears_the_pairs_failures(world):
    _fail(world, "viktima@shembull.al", 4)
    assert world.login("viktima@shembull.al").status_code == 200
    _fail(world, "viktima@shembull.al", 4)  # pa fshirje do të ishin 8 dhe i 6-ti do të bllokohej
    assert world.login("viktima@shembull.al").status_code == 200


def test_failures_expire_with_the_window(world):
    _fail(world, "viktima@shembull.al", 5)
    with world.db() as db:
        for row in db.scalars(select(LoginFailureRow)):
            row.at = row.at - timedelta(minutes=16)
        db.commit()
    assert world.login("viktima@shembull.al", PASSWORD).status_code == 200


def test_retry_after_says_when_the_oldest_blocking_failure_leaves(world):
    """Dështimet kanë moshë të ndryshme: kova hapet kur më i vjetri del nga
    dritarja (pas 1 minute), jo kur del më i riu (pas 9)."""
    _fail(world, "viktima@shembull.al", 5)
    with world.db() as db:
        rows = db.scalars(select(LoginFailureRow).order_by(LoginFailureRow.id)).all()
        for row, minutes in zip(rows, (14, 12, 10, 8, 6), strict=True):
            row.at = row.at - timedelta(minutes=minutes)
        db.commit()
    blocked = world.login("viktima@shembull.al", PASSWORD)
    assert blocked.status_code == 429
    assert 55 <= int(blocked.headers["retry-after"]) <= 60


def test_the_table_keeps_hashes_not_emails_or_addresses(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1)
    w.register("viktima@shembull.al")
    _fail(w, "viktima@shembull.al", 2, ip="203.0.113.7")
    with w.db() as db:
        rows = db.scalars(select(LoginFailureRow)).all()
    assert len(rows) == 2
    dumped = json.dumps([(r.email_key, r.ip_key) for r in rows])
    assert "viktima" not in dumped and "shembull" not in dumped and "203.0.113" not in dumped
    assert all(len(r.email_key) == 64 and len(r.ip_key) == 64 for r in rows)
    assert rows[0].email_key != rows[0].ip_key


def test_the_audit_log_marks_a_throttle_once_and_names_no_one(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1)
    w.register("viktima@shembull.al")
    _fail(w, "viktima@shembull.al", 5, ip="203.0.113.7")
    for _ in range(4):
        w.login("viktima@shembull.al", WRONG, ip="203.0.113.7")
    events = w.audit("auth.login_throttled")
    assert [e.payload for e in events] == [{"bucket": "pair"}]
    assert events[0].user_id is None and events[0].document_id is None


@pytest.mark.parametrize(
    ("hops", "header", "expected"),
    [
        (0, "9.9.9.9", "10.0.0.1"),  # pa ndërmjetës të besuar, koka nuk numëron
        (1, "6.6.6.6, 9.9.9.9", "9.9.9.9"),  # ajo që klienti shkroi në fillim nuk numëron
        (2, "6.6.6.6, 9.9.9.9, 8.8.8.8", "9.9.9.9"),
        (2, "9.9.9.9", "10.0.0.1"),  # koka më e shkurtër se pritej: adresa e lidhjes
        (1, "", "10.0.0.1"),
    ],
)
def test_client_address_trusts_only_the_proxy_hops_configured(hops, header, expected):
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", header.encode())] if header else [],
        "client": ("10.0.0.1", 50000),
    }
    assert client_ip(Request(scope), hops) == expected


# --------------------------------------------------------------------
# Seancat
# --------------------------------------------------------------------


def test_a_refresh_token_is_spent_when_used(world):
    first = world.tokens("viktima@shembull.al")
    second = world.refresh(first["refresh_token"])
    assert second.status_code == 200
    assert second.json()["refresh_token"] != first["refresh_token"]
    assert world.me(second.json()["access_token"]).status_code == 200


def test_reuse_inside_the_grace_window_is_refused_without_revoking(world):
    first = world.tokens("viktima@shembull.al")
    second = world.refresh(first["refresh_token"]).json()
    assert world.refresh(first["refresh_token"]).status_code == 401
    assert world.me(second["access_token"]).status_code == 200
    assert world.refresh(second["refresh_token"]).status_code == 200


def test_reuse_after_the_grace_window_revokes_the_whole_session(tmp_path):
    w = World(tmp_path, refresh_reuse_grace_seconds=0)
    w.register("viktima@shembull.al")
    other_device = w.tokens("viktima@shembull.al")
    first = w.tokens("viktima@shembull.al")
    second = w.refresh(first["refresh_token"]).json()

    assert w.refresh(first["refresh_token"]).status_code == 401  # kopja e dytë e tokenit

    assert w.me(second["access_token"]).status_code == 401  # edhe aksesi i seancës
    assert w.refresh(second["refresh_token"]).status_code == 401  # edhe rifreskimi
    assert w.me(other_device["access_token"]).status_code == 200  # seanca tjetër mbetet

    events = w.audit("auth.session_revoked")
    assert [e.payload for e in events] == [{"reason": "refresh_reuse"}]


def test_logout_revokes_access_and_refresh_at_once(world):
    mine = world.tokens("viktima@shembull.al")
    other = world.tokens("viktima@shembull.al")

    out = world.client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {mine['access_token']}"}
    )
    assert out.status_code == 204
    assert world.me(mine["access_token"]).status_code == 401
    assert world.refresh(mine["refresh_token"]).status_code == 401
    assert world.me(other["access_token"]).status_code == 200
    assert [e.payload for e in world.audit("auth.session_revoked")] == [{"reason": "logout"}]


def test_logout_needs_a_valid_access_token(world):
    assert world.client.post("/auth/logout").status_code == 401
    tokens = world.tokens("viktima@shembull.al")
    as_refresh = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert world.client.post("/auth/logout", headers=as_refresh).status_code == 401


def test_tokens_from_before_sessions_existed_are_refused(world):
    with world.db() as db:
        user_id = db.scalars(select(UserRow)).first().id
    now = datetime.now(UTC)

    def legacy(kind: str) -> str:
        payload = {"sub": str(user_id), "typ": kind, "iat": now, "exp": now + timedelta(days=1)}
        return jwt.encode(payload, world.settings.jwt_secret, algorithm="HS256")

    assert world.me(legacy("access")).status_code == 401
    assert world.refresh(legacy("refresh")).status_code == 401


def test_a_token_for_a_session_that_never_existed_is_refused(world):
    from uuid import uuid4

    with world.db() as db:
        user_id = db.scalars(select(UserRow)).first().id
    now = datetime.now(UTC)
    forged = jwt.encode(
        {
            "sub": str(user_id),
            "typ": "access",
            "sid": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(days=1),
        },
        world.settings.jwt_secret,
        algorithm="HS256",
    )
    assert world.me(forged).status_code == 401


def test_a_session_belongs_to_the_user_who_opened_it(world):
    """Një token me `sub` të një përdoruesi dhe `sid` të një tjetri nuk kalon."""
    world.register("tjeter@shembull.al")
    world.tokens("tjeter@shembull.al")
    with world.db() as db:
        victim_id = db.scalars(select(UserRow).where(UserRow.email == "viktima@shembull.al")).one().id
        others_session = db.scalars(
            select(AuthSessionRow).where(AuthSessionRow.user_id != victim_id)
        ).one()
        others_session_id = others_session.id
    now = datetime.now(UTC)
    mixed = jwt.encode(
        {
            "sub": str(victim_id),
            "typ": "access",
            "sid": str(others_session_id),
            "iat": now,
            "exp": now + timedelta(days=1),
        },
        world.settings.jwt_secret,
        algorithm="HS256",
    )
    assert world.me(mixed).status_code == 401


def test_expired_refresh_rows_are_removed_at_the_next_login(world):
    world.tokens("viktima@shembull.al")
    with world.db() as db:
        for row in db.scalars(select(RefreshTokenRow)):
            row.expires_at = datetime.now(UTC) - timedelta(days=1)
        db.commit()
    world.tokens("viktima@shembull.al")
    with world.db() as db:
        assert len(db.scalars(select(RefreshTokenRow)).all()) == 1


def test_the_revocation_survives_the_401_that_reports_it(tmp_path):
    """Sesioni i kërkesës kthen prapa çdo gjë kur kërkesa përfundon me 401;
    revokimi duhet të ruhet para tij, përndryshe ripërdorimi nuk revokon asgjë."""
    w = World(tmp_path, refresh_reuse_grace_seconds=0)
    w.register("viktima@shembull.al")
    first = w.tokens("viktima@shembull.al")
    w.refresh(first["refresh_token"])
    assert w.refresh(first["refresh_token"]).status_code == 401
    with w.db() as db:
        session = db.scalars(select(AuthSessionRow)).one()
        assert session.revoked_at is not None
        assert session.revoked_reason == "refresh_reuse"


# --------------------------------------------------------------------
# IPv6: numërimi sipas prefiksit (ADR 0014)
# --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("address", "bits", "expected"),
    [
        ("2001:db8:1:2:aaaa:bbbb:cccc:dddd", 64, "2001:db8:1:2::/64"),
        ("2001:db8:1:2::1", 64, "2001:db8:1:2::/64"),  # e njëjta rrjetë, adresë tjetër
        ("2001:db8:1:3::1", 64, "2001:db8:1:3::/64"),  # /64 tjetër
        ("2001:db8:1:2::1", 48, "2001:db8:1::/48"),
        ("::ffff:203.0.113.7", 64, "203.0.113.7"),  # IPv4 e mapuar numërohet si IPv4
        ("203.0.113.7", 64, "203.0.113.7"),  # IPv4 e plotë
        ("panjohur", 64, "panjohur"),
    ],
)
def test_addresses_are_counted_by_network(address, bits, expected):
    assert network_of(address, bits) == expected


def test_the_client_address_is_reduced_to_its_prefix():
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"6.6.6.6, 2001:db8:1:2:aaaa:bbbb:cccc:dddd")],
        "client": ("10.0.0.1", 50000),
    }
    assert client_ip(Request(scope), 1) == "2001:db8:1:2::/64"
    assert client_ip(Request(scope), 1, 48) == "2001:db8:1::/48"


def test_failures_from_one_slash_64_share_the_buckets(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1)
    w.register("viktima@shembull.al")
    for i in range(5):  # pesë adresa të ndryshme, e njëjta /64
        assert w.login("viktima@shembull.al", WRONG, ip=f"2001:db8:1:2::{i + 1}").status_code == 401
    # i gjashti nga një adresë e gjashtë të së njëjtës /64 bllokohet, edhe me fjalëkalimin e saktë
    assert w.login("viktima@shembull.al", PASSWORD, ip="2001:db8:1:2:ffff::9").status_code == 429
    # një /64 tjetër nuk preket
    assert w.login("viktima@shembull.al", PASSWORD, ip="2001:db8:1:3::1").status_code == 200


def test_one_slash_64_cannot_spray_many_accounts_by_rotating_addresses(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1, login_max_failures_ip=6)
    for i in range(6):
        assert w.login(f"nje{i}@shembull.al", WRONG, ip=f"2001:db8:1:2::{i + 1}").status_code == 401
    assert w.login("tjeter@shembull.al", WRONG, ip="2001:db8:1:2::ff").status_code == 429
    assert w.login("tjeter@shembull.al", WRONG, ip="2001:db8:9:9::1").status_code == 401


# --------------------------------------------------------------------
# Dil kudo
# --------------------------------------------------------------------


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_logout_all_revokes_every_session_of_the_user_and_only_theirs(world):
    world.register("tjeter@shembull.al")
    first = world.tokens("viktima@shembull.al")
    second = world.tokens("viktima@shembull.al")
    third = world.tokens("viktima@shembull.al")
    other = world.tokens("tjeter@shembull.al")

    out = world.client.post("/auth/logout-all", headers=_bearer(first["access_token"]))
    assert out.status_code == 204

    for tokens in (first, second, third):
        assert world.me(tokens["access_token"]).status_code == 401
        assert world.refresh(tokens["refresh_token"]).status_code == 401
    assert world.me(other["access_token"]).status_code == 200  # përdorues tjetër: i paprekur
    assert [e.payload for e in world.audit("auth.sessions_revoked_all")] == [{"count": 3}]
    with world.db() as db:
        reasons = {s.revoked_reason for s in db.scalars(select(AuthSessionRow)) if s.revoked_at}
        assert reasons == {"logout_all"}
    # hyrja e re funksionon
    assert world.login("viktima@shembull.al").status_code == 200


def test_logout_all_counts_only_the_sessions_that_were_still_open(world):
    first = world.tokens("viktima@shembull.al")
    second = world.tokens("viktima@shembull.al")
    world.client.post("/auth/logout", headers=_bearer(second["access_token"]))
    world.client.post("/auth/logout-all", headers=_bearer(first["access_token"]))
    assert [e.payload for e in world.audit("auth.sessions_revoked_all")] == [{"count": 1}]


def test_logout_all_needs_a_valid_access_token(world):
    assert world.client.post("/auth/logout-all").status_code == 401
    tokens = world.tokens("viktima@shembull.al")
    assert world.client.post("/auth/logout-all", headers=_bearer(tokens["refresh_token"])).status_code == 401
    assert world.me(tokens["access_token"]).status_code == 200  # nuk u revokua asgjë
