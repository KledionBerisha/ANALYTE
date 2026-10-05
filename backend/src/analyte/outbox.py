"""
Tokenët e lidhjeve me email, dërgimi me rishikim dhe rindërgimi i mesazheve të humbura (ADR 0018).

**Problemi.** Lidhja ruhet në bazë para se mesazhi të nisë (ADR 0016), dhe mesazhi nis nga një detyrë në sfond
pas përgjigjes. Nëse transporti dështon, ose procesi ndalet midis ruajtjes dhe dërgimit, tokeni ekziston por
mesazhi s'ka mbërritur, dhe përdoruesi duhet ta kërkojë vetë një të ri.

**Regjistri i dërgimit.** Çdo mesazh me lidhje (konfirmim, rivendosje) ka një rresht te `mail_deliveries`: lloji,
tokeni që mbart (`token_id`), sa herë u provua dhe lloji i gabimit të fundit. Rreshti nuk mban adresë, lidhje apo
tekst; adresa nxirret nga `users` kur duhet.

**Rishikimi në sfond** (`deliver`): dërgimi provohet deri `mail_send_attempts` herë me pritje që dyfishohet. Një
dështim përfundimtar lë rreshtin `pending` dhe një ngjarje auditimi me llojin e gabimit.

**Kalimi periodik** (`resend_unsent`, i thirrur nga punëtori arq): merr mesazhet `pending` që kanë pritur
`mail_resend_after_minutes`. **Tokeni i vjetër nuk rikthehet**: ruhet vetëm si HMAC, prandaj lidhja e plotë nuk
mund të ndërtohet sërish, dhe të ruhej e pastër do ta prishte vetinë që një kopje e bazës nuk jep lidhje të
përdorshme. Prandaj kalimi lëshon një token të ri (që shfuqizon të vjetrin të papërdorur), dërgon lidhjen e re,
dhe e shënon rreshtin e vjetër `superseded`. Kufijtë:

  - vetëm mesazhet me token të papërdorur dhe të pa skaduar (ndryshe `expired`: s'ka çfarë të dërgohet);
  - jo më shumë se `mail_auto_reissue_per_day` rilëshime automatike për një përdorues në 24 orë, që kalimi të mos
    përdoret për të mbushur një kuti postare (tejkalimi shënohet `skipped`);
  - `limit` mesazhe për kalim.
"""

from __future__ import annotations

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import NamedTuple
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from analyte import mail
from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.persistence.tables import (
    EmailConfirmationRow,
    MailDeliveryRow,
    PasswordResetRow,
    UserRow,
)
from analyte.security import keyed_hash

CONFIRMATION = "confirmation"
PASSWORD_RESET = "password_reset"

PENDING = "pending"
SENT = "sent"
SUPERSEDED = "superseded"
EXPIRED = "expired"
SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class Outgoing:
    """Një mesazh gati për t'u dërguar. Mban adresën dhe tekstin me lidhjen, prandaj nuk shkruhet te log-u."""

    to: str = field(repr=False)
    subject: str = field(repr=False)
    body: str = field(repr=False)
    delivery_id: UUID | None = None
    """Bosh për mesazhet pa token (njoftimi «ky email ka tashmë llogari»): s'ka çfarë të rindërgohet."""


class Issued(NamedTuple):
    token: str
    token_id: UUID


# --------------------------------------------------------------------
# Tokenët dhe mesazhet
# --------------------------------------------------------------------


def _base(config: Settings) -> str:
    return config.frontend_url.rstrip("/")


def confirmation_link(config: Settings, token: str) -> str:
    return f"{_base(config)}/confirm?token={token}"


def reset_link(config: Settings, token: str) -> str:
    return f"{_base(config)}/reset-password?token={token}"


def issue_confirmation(db: Session, user: UserRow, config: Settings, now: datetime) -> Issued:
    """Një lidhje e re konfirmimi. Ato të mëparshme të papërdorura shfuqizohen: vlen vetëm e fundit."""
    db.execute(
        delete(EmailConfirmationRow).where(
            EmailConfirmationRow.user_id == user.id, EmailConfirmationRow.used_at.is_(None)
        )
    )
    token = secrets.token_urlsafe(32)
    row = EmailConfirmationRow(
        user_id=user.id,
        token_key=keyed_hash(config.jwt_secret, "email-confirm", token),
        created_at=now,
        expires_at=now + timedelta(hours=config.confirm_token_hours),
    )
    db.add(row)
    db.flush()
    return Issued(token, row.id)


def issue_password_reset(db: Session, user: UserRow, config: Settings, now: datetime) -> Issued:
    """Një lidhje e re rivendosjeje. Ato të mëparshme të papërdorura shfuqizohen, si te konfirmimi."""
    db.execute(
        delete(PasswordResetRow).where(
            PasswordResetRow.user_id == user.id, PasswordResetRow.used_at.is_(None)
        )
    )
    token = secrets.token_urlsafe(32)
    row = PasswordResetRow(
        user_id=user.id,
        token_key=keyed_hash(config.jwt_secret, "password-reset", token),
        created_at=now,
        expires_at=now + timedelta(minutes=config.reset_token_minutes),
    )
    db.add(row)
    db.flush()
    return Issued(token, row.id)


def _record_delivery(
    db: Session, user: UserRow, kind: str, token_id: UUID, origin: str, now: datetime
) -> UUID:
    row = MailDeliveryRow(
        user_id=user.id, kind=kind, token_id=token_id, origin=origin, status=PENDING, created_at=now
    )
    db.add(row)
    db.flush()
    return row.id


def prepare_confirmation(
    db: Session, user: UserRow, config: Settings, now: datetime, origin: str = "request"
) -> Outgoing:
    """Lëshon tokenin, e regjistron dërgimin dhe ndërton mesazhin. Thirrësi e ruan (`commit`) para dërgimit."""
    issued = issue_confirmation(db, user, config, now)
    subject, body = mail.confirmation_message(
        confirmation_link(config, issued.token), config.confirm_token_hours
    )
    delivery = _record_delivery(db, user, CONFIRMATION, issued.token_id, origin, now)
    return Outgoing(user.email, subject, body, delivery)


def prepare_password_reset(
    db: Session, user: UserRow, config: Settings, now: datetime, origin: str = "request"
) -> Outgoing:
    issued = issue_password_reset(db, user, config, now)
    subject, body = mail.password_reset_message(
        reset_link(config, issued.token), config.reset_token_minutes
    )
    delivery = _record_delivery(db, user, PASSWORD_RESET, issued.token_id, origin, now)
    return Outgoing(user.email, subject, body, delivery)


# --------------------------------------------------------------------
# Dërgimi me rishikim
# --------------------------------------------------------------------


class SendResult(NamedTuple):
    attempts: int
    error: str | None
    """Lloji i gabimit të provës së fundit, ose `None` nëse mesazhi u dërgua."""


def send_with_retry(
    mailer: mail.Mailer,
    outgoing: Outgoing,
    *,
    attempts: int,
    backoff: float,
    sleep: Callable[[float], None] = time.sleep,
) -> SendResult:
    """Provon dërgimin deri `attempts` herë; pritja para provës së n-të është `backoff · 2^(n-2)`.

    Gabimi regjistrohet vetëm si lloj (`type(error).__name__`): mesazhi i tij mund të përmbajë adresën.
    """
    error: str | None = None
    attempts = max(1, attempts)
    for attempt in range(1, attempts + 1):
        try:
            mailer.send(outgoing.to, outgoing.subject, outgoing.body)
            return SendResult(attempt, None)
        except Exception as caught:  # noqa: BLE001 — çdo dështim i transportit trajtohet njësoj
            error = type(caught).__name__
            mail.log.warning("dërgimi i email-it dështoi (prova %d nga %d): %s", attempt, attempts, error)
            if attempt < attempts and backoff > 0:
                sleep(backoff * 2 ** (attempt - 1))
    return SendResult(attempts, error)


def _settle(
    sessions: sessionmaker[Session], outgoing: Outgoing, result: SendResult, now: datetime
) -> None:
    with sessions() as db:
        if outgoing.delivery_id is not None:
            row = db.get(MailDeliveryRow, outgoing.delivery_id)
            # Vetëm një rresht që ende pret: nëse kalimi periodik e zëvendësoi ndërkohë, s'ka çfarë të ndryshohet.
            if row is not None and row.status == PENDING:
                row.attempts += result.attempts
                row.last_attempt_at = now
                row.last_error = result.error
                if result.error is None:
                    row.status = SENT
                    row.sent_at = now
        if result.error is not None:
            audit.mail_failed(db, result.error)
        db.commit()


def deliver(app, outgoing: Outgoing) -> None:
    """Detyra në sfond pas përgjigjes. Një dështim përfundimtar nuk arrin te klienti: përgjigja ka dalë tashmë, dhe
    është e njëjtë për çdo email."""
    config: Settings = app.state.settings
    result = send_with_retry(
        app.state.mailer,
        outgoing,
        attempts=config.mail_send_attempts,
        backoff=config.mail_retry_backoff_seconds,
    )
    _settle(app.state.sessions, outgoing, result, datetime.now(UTC))


# --------------------------------------------------------------------
# Kalimi periodik
# --------------------------------------------------------------------


@dataclass(slots=True)
class ResendReport:
    examined: int = 0
    reissued: int = 0
    sent: int = 0
    failed: int = 0
    expired: int = 0
    skipped: int = 0


def _reissue(
    sessions: sessionmaker[Session],
    delivery_id: UUID,
    config: Settings,
    now: datetime,
    report: ResendReport,
) -> Outgoing | None:
    """Vendos çfarë ndodh me një mesazh të padërguar; kthen mesazhin e ri nëse lëshohet token i ri."""
    with sessions() as db:
        delivery = db.get(MailDeliveryRow, delivery_id)
        if delivery is None or delivery.status != PENDING:
            return None
        report.examined += 1
        user = db.get(UserRow, delivery.user_id)
        token_table = EmailConfirmationRow if delivery.kind == CONFIRMATION else PasswordResetRow
        token = db.get(token_table, delivery.token_id)
        live = user is not None and token is not None and token.used_at is None and token.expires_at > now
        if live and delivery.kind == CONFIRMATION:
            live = user.email_confirmed_at is None
        if live and delivery.kind == PASSWORD_RESET:
            live = user.email_confirmed_at is not None
        if not live:
            delivery.status = EXPIRED
            db.commit()
            report.expired += 1
            return None

        reissued_today = db.scalar(
            select(func.count())
            .select_from(MailDeliveryRow)
            .where(
                MailDeliveryRow.user_id == user.id,
                MailDeliveryRow.origin == "sweep",
                MailDeliveryRow.created_at >= now - timedelta(hours=24),
            )
        )
        if reissued_today >= config.mail_auto_reissue_per_day:
            delivery.status = SKIPPED
            db.commit()
            report.skipped += 1
            return None

        # Marrja e rreshtit është një UPDATE i kushtëzuar: dy kalime paralele nuk e rilëshojnë të dy të njëjtin mesazh.
        claimed = db.execute(
            update(MailDeliveryRow)
            .where(MailDeliveryRow.id == delivery.id, MailDeliveryRow.status == PENDING)
            .values(status=SUPERSEDED)
        ).rowcount
        if claimed == 0:
            return None
        prepare = prepare_confirmation if delivery.kind == CONFIRMATION else prepare_password_reset
        outgoing = prepare(db, user, config, now, origin="sweep")
        audit.mail_reissued(db, user.id, delivery.kind)
        db.commit()
        report.reissued += 1
        return outgoing


def resend_unsent(
    sessions: sessionmaker[Session],
    mailer: mail.Mailer,
    config: Settings,
    *,
    now: datetime | None = None,
    sleep: Callable[[float], None] = time.sleep,
    limit: int = 50,
) -> ResendReport:
    """Rindërgon mesazhet që pritën shumë pa u dërguar (shih dokumentin e modulit). I sigurt për t'u thirrur shpesh."""
    now = now or datetime.now(UTC)
    report = ResendReport()
    with sessions() as db:
        db.execute(
            delete(MailDeliveryRow).where(
                MailDeliveryRow.created_at < now - timedelta(days=config.mail_delivery_retention_days)
            )
        )
        db.commit()
        waited = now - timedelta(minutes=config.mail_resend_after_minutes)
        pending = db.scalars(
            select(MailDeliveryRow.id)
            .where(
                MailDeliveryRow.status == PENDING,
                func.coalesce(MailDeliveryRow.last_attempt_at, MailDeliveryRow.created_at) <= waited,
            )
            .order_by(MailDeliveryRow.created_at)
            .limit(limit)
        ).all()

    for delivery_id in pending:
        outgoing = _reissue(sessions, delivery_id, config, now, report)
        if outgoing is None:
            continue
        result = send_with_retry(
            mailer,
            outgoing,
            attempts=config.mail_send_attempts,
            backoff=config.mail_retry_backoff_seconds,
            sleep=sleep,
        )
        _settle(sessions, outgoing, result, now)
        if result.error is None:
            report.sent += 1
        else:
            report.failed += 1
    return report
