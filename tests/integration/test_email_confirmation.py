"""
Konfirmimi i email-it (ADR 0016).

Pohimet më të rëndësishme:

  - **Asnjë përgjigje e regjistrimit nuk tregon nëse email-i ka llogari.** Statusi dhe trupi janë të njëjtë
    për email të ri, të regjistruar dhe të pakonfirmuar; ndryshon vetëm mesazhi që merr kutia postare.
  - **Llogaria nuk hyn pa konfirmim**, dhe lidhja vlen një herë, skadon, dhe nuk ruhet si tekst.
  - **Dërgimi dështon në heshtje për klientin** (përgjigja ka dalë tashmë), por lë gjurmë pa adresë.
  - **Transporti SMTP** përdor STARTTLS dhe kredencialet, dhe shërbimi nuk nis pa konfigurim posta.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text

import analyte.api.auth as auth_module
from analyte import mail
from analyte.config import Settings
from analyte.generation.templates import TemplateGenerator
from analyte.main import create_app
from analyte.orchestration.tasks import InlineRunner, Services
from analyte.persistence.database import create_schema, make_engine, make_session_factory
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import (
    AuditEventRow,
    EmailConfirmationRow,
    LoginFailureRow,
    RegistrationAttemptRow,
    UserRow,
)
from analyte.security import keyed_hash
from tests.fixtures.mailbox import client_for, register_confirmed, token_in

PASSWORD = "fjalekalim-testi-i-gjate"
OTHER = "fjalekalim-tjeter-i-gjate"
SUBJECT_CONFIRM = "Konfirmoni email-in tuaj në ANALYTE"
SUBJECT_EXISTS = "Ky email ka tashmë llogari në ANALYTE"


class World:
    def __init__(self, tmp: Path, mailer=None, **overrides) -> None:
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
        if mailer is None:
            self.client = client_for(self.settings, self.services)
            self.outbox = self.client.outbox
        else:
            self.client = TestClient(
                create_app(self.settings, self.services, InlineRunner(self.services), mailer)
            )
            self.outbox = mailer

    def register(self, email: str, password: str = PASSWORD, ip: str | None = None):
        headers = {"X-Forwarded-For": ip} if ip else {}
        return self.client.post(
            "/auth/register", json={"email": email, "password": password}, headers=headers
        )

    def login(self, email: str, password: str = PASSWORD):
        return self.client.post("/auth/login", json={"email": email, "password": password})

    def confirm(self, token: str):
        return self.client.post("/auth/confirm", json={"token": token})

    def db(self):
        return self.services.sessions()


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


# --------------------------------------------------------------------
# Regjistrimi nuk tregon nëse email-i ka llogari
# --------------------------------------------------------------------


def test_the_three_registration_cases_get_the_same_response(world):
    world.register("konfirmuar@shembull.al")
    world.confirm(token_in(world.outbox.to("konfirmuar@shembull.al")[-1]))
    world.register("pakonfirmuar@shembull.al")

    new = world.register("i-ri@shembull.al")
    confirmed = world.register("konfirmuar@shembull.al")
    pending = world.register("pakonfirmuar@shembull.al")

    assert new.status_code == confirmed.status_code == pending.status_code == 202
    assert new.json() == confirmed.json() == pending.json() == {"message": auth_module.REGISTER_REPLY}
    assert new.headers["content-type"] == confirmed.headers["content-type"] == pending.headers["content-type"]


def test_the_mailbox_owner_learns_which_case_it_was(world):
    world.register("konfirmuar@shembull.al")
    world.confirm(token_in(world.outbox.to("konfirmuar@shembull.al")[-1]))
    world.register("konfirmuar@shembull.al", OTHER)  # dikush tjetër provon me këtë email

    subjects = [m.subject for m in world.outbox.to("konfirmuar@shembull.al")]
    assert subjects == [SUBJECT_CONFIRM, SUBJECT_EXISTS]
    assert "/confirm?token=" not in world.outbox.to("konfirmuar@shembull.al")[-1].body
    # llogaria ekzistuese nuk ndryshoi: fjalëkalimi i vjetër hyn, ai i ri jo
    assert world.login("konfirmuar@shembull.al", PASSWORD).status_code == 200
    assert world.login("konfirmuar@shembull.al", OTHER).status_code == 401


def test_argon2_is_spent_in_every_case_so_timing_does_not_show_which(world, monkeypatch):
    calls = []
    real = auth_module.hash_password
    monkeypatch.setattr(auth_module, "hash_password", lambda p: calls.append(p) or real(p))
    world.register("a@shembull.al")  # i ri
    world.register("a@shembull.al")  # i pakonfirmuar
    world.confirm(token_in(world.outbox.to("a@shembull.al")[-1]))
    world.register("a@shembull.al")  # i konfirmuar
    assert len(calls) == 3


# --------------------------------------------------------------------
# Hyrja pa konfirmim dhe vetë konfirmimi
# --------------------------------------------------------------------


def test_an_unconfirmed_account_cannot_sign_in_and_the_attempt_is_not_a_failure(world):
    world.register("viktima@shembull.al")
    denied = world.login("viktima@shembull.al")
    assert denied.status_code == 403
    assert denied.headers["content-type"].startswith("application/problem+json")
    # me fjalëkalim të gabuar mbetet 401 i zakonshëm, i njëjtë me atë të email-it të panjohur
    assert world.login("viktima@shembull.al", OTHER).status_code == 401
    assert world.login("askush@shembull.al", OTHER).status_code == 401
    with world.db() as db:
        # vetëm dy dështimet e vërteta; 403-ja nuk numërohet
        assert len(list(db.scalars(select(LoginFailureRow)))) == 2


def test_confirming_opens_the_account(world):
    world.register("viktima@shembull.al")
    assert world.confirm(token_in(world.outbox.to("viktima@shembull.al")[-1])).status_code == 204
    assert world.login("viktima@shembull.al").status_code == 200
    with world.db() as db:
        user = db.scalars(select(UserRow)).one()
        assert user.email_confirmed_at is not None
        events = [e.event_type for e in db.scalars(select(AuditEventRow))]
        assert "user.email_confirmed" in events


def test_the_link_works_once(world):
    world.register("viktima@shembull.al")
    token = token_in(world.outbox.to("viktima@shembull.al")[-1])
    assert world.confirm(token).status_code == 204
    again = world.confirm(token)
    assert again.status_code == 400


def test_unknown_used_and_expired_tokens_get_the_same_error(tmp_path):
    w = World(tmp_path, confirm_token_hours=0)  # skadon në çast
    w.register("viktima@shembull.al")
    expired = w.confirm(token_in(w.outbox.to("viktima@shembull.al")[-1]))
    unknown = w.confirm("x" * 43)
    assert expired.status_code == unknown.status_code == 400
    assert expired.json()["title"] == unknown.json()["title"]
    assert w.login("viktima@shembull.al").status_code == 403  # nuk u konfirmua


def test_the_token_is_never_stored_in_clear(world):
    world.register("viktima@shembull.al")
    token = token_in(world.outbox.to("viktima@shembull.al")[-1])
    with world.db() as db:
        row = db.scalars(select(EmailConfirmationRow)).one()
        assert token not in row.token_key
        assert row.token_key == keyed_hash("t" * 48, "email-confirm", token)
        # ndryshon sipas etiketës: HMAC-u i të njëjtës vlerë për një qëllim tjetër s'është ky
        assert row.token_key != keyed_hash("t" * 48, "login-email", token)


def test_registering_again_before_confirming_replaces_the_password_and_the_link(world):
    world.register("viktima@shembull.al", OTHER)  # dikush regjistron email-in e tjetrit më parë
    old_token = token_in(world.outbox.to("viktima@shembull.al")[-1])
    world.register("viktima@shembull.al", PASSWORD)  # zotëruesi regjistrohet vërtet
    new_token = token_in(world.outbox.to("viktima@shembull.al")[-1])

    assert world.confirm(old_token).status_code == 400  # lidhja e vjetër nuk vlen më
    assert world.confirm(new_token).status_code == 204
    assert world.login("viktima@shembull.al", PASSWORD).status_code == 200
    assert world.login("viktima@shembull.al", OTHER).status_code == 401


def test_a_token_confirms_only_its_own_account(world):
    world.register("e-para@shembull.al")
    world.register("e-dyta@shembull.al")
    world.confirm(token_in(world.outbox.to("e-para@shembull.al")[-1]))
    assert world.login("e-para@shembull.al").status_code == 200
    assert world.login("e-dyta@shembull.al").status_code == 403


# --------------------------------------------------------------------
# Ridërgimi
# --------------------------------------------------------------------


def test_resend_gives_a_pending_account_a_new_link_and_everyone_else_the_same_answer(world):
    world.register("pakonfirmuar@shembull.al")
    world.register("konfirmuar@shembull.al")
    world.confirm(token_in(world.outbox.to("konfirmuar@shembull.al")[-1]))
    first = token_in(world.outbox.to("pakonfirmuar@shembull.al")[-1])

    answers = [
        world.client.post("/auth/resend-confirmation", json={"email": e})
        for e in ("pakonfirmuar@shembull.al", "konfirmuar@shembull.al", "askush@shembull.al")
    ]
    assert {a.status_code for a in answers} == {202}
    assert answers[0].json() == answers[1].json() == answers[2].json()
    assert len(world.outbox.to("pakonfirmuar@shembull.al")) == 2
    assert len(world.outbox.to("konfirmuar@shembull.al")) == 1  # nuk mori asgjë të re
    assert world.outbox.to("askush@shembull.al") == []

    assert world.confirm(first).status_code == 400  # e para u shfuqizua nga e reja
    assert world.confirm(token_in(world.outbox.to("pakonfirmuar@shembull.al")[-1])).status_code == 204


# --------------------------------------------------------------------
# Kufizimi i email-eve që nis shërbimi
# --------------------------------------------------------------------


def test_one_address_gets_at_most_three_requests_an_hour(world):
    for _ in range(3):
        assert world.register("viktima@shembull.al").status_code == 202
    blocked = world.register("viktima@shembull.al")
    assert blocked.status_code == 429
    assert 1 <= int(blocked.headers["retry-after"]) <= 3600
    assert len(world.outbox.to("viktima@shembull.al")) == 3  # kërkesa e refuzuar nuk dërgoi asgjë


def test_the_limit_does_not_depend_on_whether_the_email_has_an_account(world):
    world.register("ekziston@shembull.al")
    world.confirm(token_in(world.outbox.to("ekziston@shembull.al")[-1]))
    for email in ("ekziston@shembull.al", "nuk-ekziston@shembull.al"):
        for _ in range(3 - (1 if email.startswith("ekziston") else 0)):
            world.register(email)
    known = world.register("ekziston@shembull.al")
    unknown = world.register("nuk-ekziston@shembull.al")
    assert known.status_code == unknown.status_code == 429
    assert known.json()["title"] == unknown.json()["title"]


def test_one_ip_cannot_mail_many_addresses(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1, register_max_per_ip=4)
    for i in range(4):
        assert w.register(f"p{i}@shembull.al", ip="203.0.113.7").status_code == 202
    assert w.register("p9@shembull.al", ip="203.0.113.7").status_code == 429
    assert w.register("p9@shembull.al", ip="203.0.113.8").status_code == 202  # IP tjetër


def test_the_attempts_table_holds_no_email_and_no_address(world):
    world.register("viktima@shembull.al")
    with world.db() as db:
        rows = list(db.scalars(select(RegistrationAttemptRow)))
        assert len(rows) == 1
        assert "viktima" not in rows[0].email_key and "shembull" not in rows[0].email_key
        assert rows[0].email_key == keyed_hash("t" * 48, "register-email", "viktima@shembull.al")
        dump = " ".join(str(v) for e in db.scalars(select(AuditEventRow)) for v in (e.payload or {}).values())
        assert "viktima" not in dump


# --------------------------------------------------------------------
# Dërgimi dështon
# --------------------------------------------------------------------


class Broken:
    def send(self, to: str, subject: str, body: str) -> None:
        raise ConnectionRefusedError(f"SMTP i pakapshëm për {to}")


def test_a_mail_failure_does_not_change_the_response_and_leaves_a_trace_without_the_address(tmp_path):
    w = World(tmp_path, mailer=Broken())
    response = w.register("viktima@shembull.al")
    assert response.status_code == 202
    assert response.json() == {"message": auth_module.REGISTER_REPLY}
    with w.db() as db:
        failed = [e for e in db.scalars(select(AuditEventRow)) if e.event_type == "mail.failed"]
        assert [e.payload for e in failed] == [{"error_type": "ConnectionRefusedError"}]
        assert "viktima" not in str([e.payload for e in db.scalars(select(AuditEventRow))])
    # llogaria u krijua dhe mund të kërkohet një lidhje e re
    assert w.login("viktima@shembull.al").status_code == 403


# --------------------------------------------------------------------
# Transporti SMTP
# --------------------------------------------------------------------


class FakeSmtp:
    instances: list["FakeSmtp"] = []

    def __init__(self, host, port, timeout=None, context=None):
        self.host, self.port, self.timeout, self.context = host, port, timeout, context
        self.calls: list[tuple] = []
        FakeSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        self.calls.append(("starttls", context is not None))

    def login(self, user, password):
        self.calls.append(("login", user, password))

    def send_message(self, message):
        self.calls.append(("send", message["From"], message["To"], message["Subject"], message.get_content()))


@pytest.fixture
def fake_smtp(monkeypatch):
    FakeSmtp.instances = []
    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSmtp)
    monkeypatch.setattr(mail.smtplib, "SMTP_SSL", FakeSmtp)
    return FakeSmtp


def test_smtp_uses_starttls_then_login_then_sends_a_plain_message(fake_smtp):
    mailer = mail.SmtpMailer(
        "sandbox.smtp.mailtrap.io", 2525, "ANALYTE <noreply@analyte.local>",
        username="përdoruesi", password="sekret",
    )
    mailer.send("viktima@shembull.al", "Tema", "Trupi")
    smtp = fake_smtp.instances[0]
    assert (smtp.host, smtp.port) == ("sandbox.smtp.mailtrap.io", 2525)
    assert [c[0] for c in smtp.calls] == ["starttls", "login", "send"]
    assert smtp.calls[0] == ("starttls", True)
    assert smtp.calls[1] == ("login", "përdoruesi", "sekret")
    _, sender, to, subject, body = smtp.calls[2]
    assert (sender, to, subject) == ("ANALYTE <noreply@analyte.local>", "viktima@shembull.al", "Tema")
    assert body.strip() == "Trupi"


def test_smtp_security_modes(fake_smtp):
    mail.SmtpMailer("h", 465, "a@b.al", security="ssl").send("x@y.al", "T", "B")
    assert [c[0] for c in fake_smtp.instances[0].calls] == ["send"]  # SSL i tërë: pa STARTTLS, pa hyrje
    mail.SmtpMailer("h", 25, "a@b.al", security="none", username="u", password="p").send("x@y.al", "T", "B")
    assert [c[0] for c in fake_smtp.instances[1].calls] == ["login", "send"]  # pa STARTTLS


def test_the_service_refuses_to_start_without_mail_configuration(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'a.db'}", jwt_secret="t" * 48,
        storage_key=Fernet.generate_key().decode(), storage_dir=tmp_path / "s", job_runner="inline", ocr=False,
    )
    with pytest.raises(mail.MailConfigError, match="ANALYTE_SMTP_HOST"):
        mail.build_mailer(settings)
    configured = settings.model_copy(update={"smtp_host": "sandbox.smtp.mailtrap.io", "smtp_username": "u"})
    assert isinstance(mail.build_mailer(configured), mail.SmtpMailer)
    console = settings.model_copy(update={"mail_backend": "console"})
    assert isinstance(mail.build_mailer(console), mail.ConsoleMailer)


def test_messages_carry_the_link_and_no_secret(world):
    world.register("viktima@shembull.al")
    body = world.outbox.to("viktima@shembull.al")[-1].body
    assert "http://localhost:3000/confirm?token=" in body
    assert "24 orë" in body
    assert PASSWORD not in body


# --------------------------------------------------------------------
# Migrimi: llogaritë ekzistuese nuk mbyllen jashtë
# --------------------------------------------------------------------


def test_accounts_that_existed_before_the_migration_are_treated_as_confirmed(tmp_path, monkeypatch):
    backend = Path(__file__).resolve().parents[2] / "backend"
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("ANALYTE_DATABASE_URL", url)
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "alembic"))
    config.set_main_option("sqlalchemy.url", url)

    command.upgrade(config, "0002")
    engine = create_engine(url)
    created = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO users (id, email, password_hash, created_at) VALUES (:i, :e, :p, :c)"),
            {"i": "11111111-1111-1111-1111-111111111111", "e": "vjeter@shembull.al", "p": "x", "c": created.isoformat(sep=" ")},
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        confirmed = connection.execute(text("SELECT email_confirmed_at, created_at FROM users")).one()
    assert confirmed[0] is not None and confirmed[0] == confirmed[1]


def test_register_confirmed_helper_leaves_a_signed_in_capable_account(world):
    register_confirmed(world.client, "ndihmes@shembull.al", PASSWORD)
    assert world.login("ndihmes@shembull.al").status_code == 200
