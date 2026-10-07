"""
Fshirja e të dhënave: një dokument, një llogari, ose çdo dokument që ka kaluar afatin e ruajtjes (ADR 0019).

"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, sessionmaker

from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.persistence.database import session_scope
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import (
    AuditEventRow,
    AuthSessionRow,
    DocumentRow,
    EmailConfirmationRow,
    LoginFailureRow,
    RefreshTokenRow,
    RegistrationAttemptRow,
    UserRow,
)
from analyte.security import keyed_hash

log = logging.getLogger(__name__)


def erase_documents(
    session: Session,
    store: EncryptedStore,
    documents: Sequence[DocumentRow],
    *,
    expired_after_days: int | None = None,
) -> int:
    """Fshin dokumentet, skedarët e tyre dhe gjithçka të derivuar; kthen sa u fshinë.

    Thirrësi e ruan transaksionin. `expired_after_days` e shënon fshirjen si skadim të afatit, jo si kërkesë të pronarit.
    """
    if not documents:
        return 0
    ids = [document.id for document in documents]
    paths = [document.storage_path for document in documents]

    for document in documents:
        if expired_after_days is None:
            audit.document_deleted(session, document.id, document.user_id)
        else:
            audit.document_expired(session, document.id, document.user_id, expired_after_days)

    session.flush()
    uploads = session.scalars(
        select(AuditEventRow).where(
            AuditEventRow.event_type == "document.uploaded", AuditEventRow.document_id.in_(ids)
        )
    ).all()
    for event in uploads:
        event.payload = {key: value for key, value in event.payload.items() if key != "sha256"}

    session.execute(delete(DocumentRow).where(DocumentRow.id.in_(ids)))
    session.flush()
    for path in paths:
        store.delete(path)
    return len(ids)


def erase_user(session: Session, store: EncryptedStore, user: UserRow, config: Settings) -> int:
    """Fshin llogarinë: dokumentet, seancat, tokenët, numëruesit e kufizimit dhe përdoruesin. Kthen sa dokumente u fshinë.

    Thirrësi e ruan transaksionin dhe e ka verifikuar fjalëkalimin.
    """
    user_id, email = user.id, user.email

    # Dokumentet rilexohen deri sa të mos mbetet asnjë: një ngarkim që u ruajt pas leximit të parë do të shkonte me
    # kaskadë pa u hequr skedari i tij.
    erased = 0
    for _ in range(3):
        documents = session.scalars(select(DocumentRow).where(DocumentRow.user_id == user_id)).all()
        if not documents:
            break
        erased += erase_documents(session, store, documents)

    sessions_of_user = select(AuthSessionRow.id).where(AuthSessionRow.user_id == user_id)
    session.execute(delete(RefreshTokenRow).where(RefreshTokenRow.session_id.in_(sessions_of_user)))
    session.execute(delete(AuthSessionRow).where(AuthSessionRow.user_id == user_id))
    session.execute(delete(EmailConfirmationRow).where(EmailConfirmationRow.user_id == user_id))
    # Numëruesit mbajnë një HMAC të email-it: edhe ai është e dhënë e llogarisë dhe hiqet bashkë me të.
    session.execute(
        delete(LoginFailureRow).where(
            LoginFailureRow.email_key == keyed_hash(config.jwt_secret, "login-email", email)
        )
    )
    session.execute(
        delete(RegistrationAttemptRow).where(
            RegistrationAttemptRow.email_key
            == keyed_hash(config.jwt_secret, "register-email", email)
        )
    )
    session.flush()
    session.execute(
        update(AuditEventRow).where(AuditEventRow.user_id == user_id).values(user_id=None)
    )
    session.execute(delete(UserRow).where(UserRow.id == user_id))
    audit.user_erased(session, erased)
    session.flush()
    return erased


@dataclass(frozen=True, slots=True)
class PurgeResult:
    purged: int
    failed: int
    """Dokumente që kaluan afatin por nuk u fshinë (p.sh. skedari nuk hiqet). Provohen sërish herën tjetër."""


def purge_expired(
    sessions: sessionmaker[Session],
    store: EncryptedStore,
    *,
    now: datetime,
    retention_days: int,
) -> PurgeResult:
    """Fshin çdo dokument të ngarkuar para `now - retention_days`, me të njëjtën rrugë si fshirja nga pronari.

    `retention_days = 0` do të thotë pa afat: nuk fshihet asgjë. Çdo dokument ka transaksionin e vet, që një skedar që nuk
    fshihet të mos bllokojë fshirjen e të gjithë të tjerëve (dhe të mos kthejë prapa ato që u fshinë tashmë). Koha
    jepet nga thirrësi, që testet të përdorin një orë të rreme.
    """
    if retention_days <= 0:
        return PurgeResult(0, 0)
    cutoff = now - timedelta(days=retention_days)

    with session_scope(sessions) as session:
        expired = list(
            session.scalars(
                select(DocumentRow.id)
                .where(DocumentRow.uploaded_at < cutoff)
                .order_by(DocumentRow.uploaded_at)
            )
        )

    purged = failed = 0
    for document_id in expired:
        try:
            with session_scope(sessions) as session:
                document = session.get(DocumentRow, document_id)
                if document is None:
                    continue  # u fshi ndërkohë nga pronari
                purged += erase_documents(
                    session, store, [document], expired_after_days=retention_days
                )
        except Exception as error:  # noqa: BLE001 — një dokument i prishur nuk e ndalon fshirjen e të tjerëve
            failed += 1
            log.warning("fshirja e dokumentit të skaduar dështoi: %s", type(error).__name__)
    return PurgeResult(purged, failed)
