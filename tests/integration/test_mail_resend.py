"""
Dërgimi me rishikim dhe rindërgimi i mesazheve të humbura (ADR 0018).

Pohimet më të rëndësishme:

  - **Dërgimi provohet disa herë** me pritje, dhe një dështim përfundimtar lë rreshtin `pending` dhe një ngjarje
    auditimi me vetëm llojin e gabimit.
  - **Kalimi periodik lëshon token të ri**, sepse tokeni i vjetër nuk rikthehet (ruhet vetëm HMAC-u): lidhja e vjetër
    pushon, e reja vlen.
  - **Kalimi është i kufizuar**: nuk prek mesazhe të dërguara, të përdorura ose të skaduara, nuk vepron para kohës së
    pritjes, dhe nuk lëshon më shumë se kufiri ditor për përdorues.
  - **Regjistri i dërgimit nuk mban adresë, lidhje apo tekst.**
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from analyte import outbox
from analyte.mail import OutboxMailer
from analyte.persistence.tables import (
    AuditEventRow,
    EmailConfirmationRow,
    MailDeliveryRow,
    PasswordResetRow,
)
from tests.fixtures.accounts import EMAIL, NEW_PASSWORD, PASSWORD, World
from tests.fixtures.mailbox import reset_token_in, token_in


class Broken:
    """Transport që dështon gjithmonë; numëron provat."""

    def __init__(self) -> None:
        self.calls = 0

    def send(self, to: str, subject: str, body: str) -> None:
        self.calls += 1
        raise ConnectionRefusedError(f"SMTP i pakapshëm për {to}")


class Flaky:
    """Dështon `failures` herët e para, pastaj dërgon."""

    def __init__(self, failures: int) -> None:
        self.failures, self.calls, self.inner = failures, 0, OutboxMailer()

    def send(self, to: str, subject: str, body: str) -> None:
        self.calls += 1
        if self.calls <= self.failures:
            raise TimeoutError("kohë e skaduar")
        self.inner.send(to, subject, body)

    def to(self, address: str):
        return self.inner.to(address)


def _deliveries(world: World) -> list[MailDeliveryRow]:
    with world.db() as db:
        rows = list(db.scalars(select(MailDeliveryRow).order_by(MailDeliveryRow.created_at)))
        db.expunge_all()
        return rows


def _later(minutes: int = 11) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)


def _sweep(world: World, mailer, **kwargs) -> outbox.ResendReport:
    return outbox.resend_unsent(
        world.services.sessions, mailer, world.settings, sleep=lambda _s: None, **kwargs
    )


@pytest.fixture
def broken_world(tmp_path):
    """Posta nuk punon: regjistrimi krijon llogari dhe token, por asnjë mesazh nuk mbërrin."""
    mailer = Broken()
    w = World(tmp_path, mailer=mailer)
    w.mailer = mailer
    return w


# --------------------------------------------------------------------
# Rishikimi në sfond
# --------------------------------------------------------------------


def test_a_failing_transport_is_tried_the_configured_number_of_times_then_left_pending(broken_world):
    w = broken_world
    assert w.register().status_code == 202
    assert w.mailer.calls == 3  # mail_send_attempts
    (row,) = _deliveries(w)
    assert (row.status, row.attempts, row.last_error, row.origin, row.kind) == (
        "pending", 3, "ConnectionRefusedError", "request", "confirmation",
    )
    assert row.sent_at is None
    assert [e.payload for e in w.audit("mail.failed")] == [{"error_type": "ConnectionRefusedError"}]  # një, jo tri


def test_a_transient_failure_is_retried_and_the_mail_arrives(tmp_path):
    flaky = Flaky(failures=2)
    w = World(tmp_path, mailer=flaky)
    assert w.register().status_code == 202
    assert flaky.calls == 3
    assert len(flaky.to(EMAIL)) == 1
    (row,) = _deliveries(w)
    assert (row.status, row.attempts, row.last_error) == ("sent", 3, None)
    assert row.sent_at is not None
    assert w.audit("mail.failed") == []


def test_the_wait_between_attempts_doubles(monkeypatch):
    waits: list[float] = []
    mailer = Broken()
    result = outbox.send_with_retry(
        mailer, outbox.Outgoing("a@b.al", "T", "B"), attempts=4, backoff=2.0, sleep=waits.append
    )
    assert waits == [2.0, 4.0, 8.0]  # pa pritje pas provës së fundit
    assert result == outbox.SendResult(4, "ConnectionRefusedError")


def test_the_log_keeps_the_error_type_and_never_the_address(broken_world, caplog):
    with caplog.at_level("WARNING", logger="analyte.mail"):
        broken_world.register()
    assert "ConnectionRefusedError" in caplog.text
    assert "viktima" not in caplog.text and "shembull" not in caplog.text


def test_the_message_is_not_written_to_a_repr(broken_world):
    out = outbox.Outgoing("viktima@shembull.al", "Tema", "lidhja-sekrete")
    assert "viktima" not in repr(out) and "sekrete" not in repr(out)


def test_the_delivery_record_holds_no_address_link_or_text(tmp_path):
    w = World(tmp_path)
    w.register()
    w.confirmed("tjeter@shembull.al")
    w.forgot("tjeter@shembull.al")
    columns = (
        "kind", "origin", "status", "last_error",
    )
    for row in _deliveries(w):
        dump = " ".join(str(getattr(row, c)) for c in columns)
        assert "shembull" not in dump and "token" not in dump and "http" not in dump
    assert {r.kind for r in _deliveries(w)} == {"confirmation", "password_reset"}
    # asnjë kolonë e tabelës nuk është e llojit tekst i lirë
    assert {c.name for c in MailDeliveryRow.__table__.columns} == {
        "id", "user_id", "kind", "token_id", "origin", "status", "attempts", "last_error",
        "created_at", "last_attempt_at", "sent_at",
    }


def test_mails_without_a_token_are_sent_with_retry_but_have_no_record(tmp_path):
    flaky = Flaky(failures=1)
    w = World(tmp_path, mailer=flaky)
    # llogari e konfirmuar drejtpërdrejt, që regjistrimi i dytë të nisë njoftimin «ky email ka tashmë llogari»
    from analyte.persistence.tables import UserRow
    from analyte.security import hash_password

    with w.db() as db:
        db.add(UserRow(email=EMAIL, password_hash=hash_password(PASSWORD), email_confirmed_at=datetime.now(UTC)))
        db.commit()
    w.register()
    assert flaky.calls == 2 and len(flaky.to(EMAIL)) == 1
    assert _deliveries(w) == []


# --------------------------------------------------------------------
# Kalimi periodik
# --------------------------------------------------------------------


def test_the_sweep_issues_a_fresh_token_and_the_old_link_stops_working(broken_world):
    w = broken_world
    w.register()
    with w.db() as db:
        old_key = db.scalars(select(EmailConfirmationRow)).one().token_key

    working = OutboxMailer()
    report = _sweep(w, working, now=_later())
    assert (report.examined, report.reissued, report.sent, report.failed) == (1, 1, 1, 0)

    (message,) = working.to(EMAIL)
    new_token = token_in(message)
    with w.db() as db:
        row = db.scalars(select(EmailConfirmationRow)).one()  # i vjetri u shfuqizua, vetëm i riu mbetet
        assert row.token_key != old_key
    first, second = _deliveries(w)
    assert (first.status, first.origin) == ("superseded", "request")
    assert (second.status, second.origin, second.attempts) == ("sent", "sweep", 1)
    # lidhja e re konfirmon llogarinë dhe llogaria hyn
    assert w.client.post("/auth/confirm", json={"token": new_token}).status_code == 204
    assert w.login().status_code == 200
    assert [e.payload for e in w.audit("mail.reissued")] == [{"kind": "confirmation"}]


def test_the_sweep_does_not_act_before_the_wait_has_passed(broken_world):
    broken_world.register()
    working = OutboxMailer()
    report = _sweep(broken_world, working, now=_later(5))  # mail_resend_after_minutes = 10
    assert report.examined == 0 and working.sent == []
    assert _deliveries(broken_world)[0].status == "pending"


def test_the_sweep_leaves_sent_mail_alone(tmp_path):
    w = World(tmp_path)
    w.register()
    working = OutboxMailer()
    assert _sweep(w, working, now=_later(60)).examined == 0
    assert working.sent == [] and len(w.outbox.to(EMAIL)) == 1


def test_a_used_link_is_marked_expired_and_nothing_is_sent(broken_world):
    w = broken_world
    w.register()
    with w.db() as db:
        row = db.scalars(select(EmailConfirmationRow)).one()
        row.used_at = datetime.now(UTC)  # p.sh. e hapi nga një mesazh që mbërriti me rrugë tjetër
        db.commit()
    working = OutboxMailer()
    report = _sweep(w, working, now=_later())
    assert (report.examined, report.expired, report.reissued) == (1, 1, 0)
    assert working.sent == [] and _deliveries(w)[0].status == "expired"


def test_an_expired_link_is_marked_expired_and_nothing_is_sent(tmp_path):
    mailer = Broken()
    w = World(tmp_path, mailer=mailer)
    w.register()
    working = OutboxMailer()
    report = _sweep(w, working, now=datetime.now(UTC) + timedelta(hours=w.settings.confirm_token_hours + 1))
    assert (report.expired, report.reissued) == (1, 0)
    assert working.sent == []


def test_a_link_replaced_by_the_user_meanwhile_is_not_resent(broken_world):
    w = broken_world
    w.register()
    # përdoruesi kërkon vetë një lidhje të re: tokeni i vjetër fshihet, regjistri i vjetër nuk ka më ç'të rindërgojë
    w.client.post("/auth/resend-confirmation", json={"email": EMAIL})
    pending = [d for d in _deliveries(w) if d.status == "pending"]
    assert len(pending) == 2
    working = OutboxMailer()
    report = _sweep(w, working, now=_later())
    assert report.expired == 1 and report.reissued == 1  # i vjetri skadon, vetëm i fundit rilëshohet
    assert len(working.sent) == 1


def test_an_already_confirmed_account_gets_nothing(broken_world):
    w = broken_world
    w.register()
    with w.db() as db:
        from analyte.persistence.tables import UserRow

        db.scalars(select(UserRow)).one().email_confirmed_at = datetime.now(UTC)
        db.commit()
    working = OutboxMailer()
    assert _sweep(w, working, now=_later()).expired == 1
    assert working.sent == []


def test_the_daily_limit_bounds_automatic_reissues_per_user(tmp_path):
    mailer = Broken()
    w = World(tmp_path, mailer=mailer, mail_auto_reissue_per_day=2)
    w.register()
    still_broken = Broken()
    reports = [_sweep(w, still_broken, now=_later(11 * (i + 1))) for i in range(4)]
    assert [r.reissued for r in reports] == [1, 1, 0, 0]
    assert [r.skipped for r in reports] == [0, 0, 1, 0]
    assert still_broken.calls == 2 * w.settings.mail_send_attempts  # vetëm dy rilëshime u provuan
    statuses = [d.status for d in _deliveries(w)]
    assert statuses == ["superseded", "superseded", "skipped"]


def test_the_limit_is_per_user_not_global(tmp_path):
    mailer = Broken()
    w = World(tmp_path, mailer=mailer, mail_auto_reissue_per_day=1)
    w.register("a@shembull.al")
    w.register("b@shembull.al")
    working = OutboxMailer()
    report = _sweep(w, working, now=_later())
    assert report.reissued == 2 and {m.to for m in working.sent} == {"a@shembull.al", "b@shembull.al"}


def test_the_sweep_handles_at_most_limit_messages_per_run(tmp_path):
    mailer = Broken()
    w = World(tmp_path, mailer=mailer)
    for i in range(4):
        w.register(f"p{i}@shembull.al", ip=None)
    working = OutboxMailer()
    report = _sweep(w, working, now=_later(), limit=3)
    assert report.examined == 3


def test_a_sweep_that_still_cannot_send_leaves_the_new_record_pending(broken_world):
    w = broken_world
    w.register()
    report = _sweep(w, Broken(), now=_later())
    assert (report.reissued, report.sent, report.failed) == (1, 0, 1)
    last = _deliveries(w)[-1]
    assert (last.status, last.origin, last.last_error) == ("pending", "sweep", "ConnectionRefusedError")


def test_the_sweep_resends_password_reset_mail_too_with_a_fresh_token(tmp_path):
    flaky = Flaky(failures=0)
    w = World(tmp_path, mailer=flaky)
    from analyte.persistence.tables import UserRow
    from analyte.security import hash_password

    with w.db() as db:
        db.add(UserRow(email=EMAIL, password_hash=hash_password(PASSWORD), email_confirmed_at=datetime.now(UTC)))
        db.commit()
    flaky.failures = 3  # transporti pushon pikërisht kur kërkohet rivendosja
    w.forgot()
    assert flaky.to(EMAIL) == []
    old = None
    with w.db() as db:
        old = db.scalars(select(PasswordResetRow)).one().token_key

    working = OutboxMailer()
    report = _sweep(w, working, now=_later())
    assert (report.reissued, report.sent) == (1, 1)
    (message,) = working.to(EMAIL)
    assert "/reset-password?token=" in message.body
    with w.db() as db:
        assert db.scalars(select(PasswordResetRow)).one().token_key != old
    assert w.reset(reset_token_in(message)).status_code == 204
    assert w.login(EMAIL, NEW_PASSWORD).status_code == 200


def test_the_audit_log_of_a_failed_sweep_holds_only_the_failure_kind(broken_world):
    w = broken_world
    w.register()
    _sweep(w, Broken(), now=_later())
    with w.db() as db:
        events = list(db.scalars(select(AuditEventRow).where(AuditEventRow.event_type.like("mail.%"))))
    for event in events:
        dump = str(event.payload)
        assert "shembull" not in dump and "http" not in dump and "token" not in dump
    assert {e.event_type for e in events} == {"mail.failed", "mail.reissued"}


def test_old_delivery_records_are_deleted(broken_world):
    w = broken_world
    w.register()
    _sweep(w, OutboxMailer(), now=datetime.now(UTC) + timedelta(days=w.settings.mail_delivery_retention_days + 1))
    assert _deliveries(w) == []  # regjistri i vjetër fshihet; asgjë më nuk pret


def test_the_worker_schedules_the_sweep_and_skips_it_without_mail_configuration(monkeypatch):
    monkeypatch.setenv("ANALYTE_JWT_SECRET", "w" * 48)
    monkeypatch.setenv("ANALYTE_STORAGE_KEY", "a" * 43 + "=")
    from analyte.orchestration import worker

    names = [job.name for job in worker.WorkerSettings.cron_jobs]
    assert "cron:resend_unsent_job" in names  # puna e rindërgimit është e planifikuar (bashkë me atë të fshirjes, ADR 0019)
    import asyncio

    asyncio.run(worker.resend_unsent_job({"mailer": None}))  # pa postë: nuk bën asgjë, nuk hedh
