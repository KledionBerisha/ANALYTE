"""
Log-u i auditimit (NFR2), pa të dhëna personale (NFR5).

Çdo ngjarje ka lloj dhe ngarkesë. Ngarkesa ndërtohet vetëm nga funksionet
këtu, dhe asnjëri prej tyre nuk pranon emër skedari, email, vlerë
laboratorike apo tekst të gjeneruar. Kufizimi mbahet me formë dhe jo me
disiplinë: nuk ka funksion të përgjithshëm "shkruaj çfarëdo".

Arsyet e kalimeve të gjendjes hyjnë në ngarkesë. Ato janë tekst teknik i
prodhuar nga sistemi — "3 shkelje: ungrounded_number", "OCR: 2 faqe" — dhe
jo përmbajtje e dokumentit.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from analyte.orchestration.states import Transition
from analyte.persistence.tables import AuditEventRow


def _record(
    session: Session,
    event_type: str,
    payload: dict,
    *,
    document_id: UUID | None = None,
    user_id: UUID | None = None,
) -> None:
    session.add(
        AuditEventRow(
            document_id=document_id, user_id=user_id, event_type=event_type, payload=payload
        )
    )


def user_registered(session: Session, user_id: UUID) -> None:
    _record(session, "user.registered", {}, user_id=user_id)


def login_throttled(session: Session, bucket: str) -> None:
    """Vetëm cila kovë u mbush (`pair`, `ip`, `email`). As email-i, as IP-ja:
    log-u i auditimit nuk mban asnjërën (NFR5), edhe pse kufizimi i përdor."""
    _record(session, "auth.login_throttled", {"bucket": bucket})


def session_revoked(session: Session, user_id: UUID, reason: str) -> None:
    _record(session, "auth.session_revoked", {"reason": reason}, user_id=user_id)


def document_uploaded(
    session: Session, document_id: UUID, user_id: UUID, size_bytes: int, sha256: str
) -> None:
    _record(
        session,
        "document.uploaded",
        {"size_bytes": size_bytes, "sha256": sha256},
        document_id=document_id,
        user_id=user_id,
    )


def transition(session: Session, document_id: UUID, step: Transition) -> None:
    _record(
        session,
        "state.transition",
        {
            "from": step.source.value,
            "to": step.target.value,
            "reason": step.reason,
            "attempt": step.attempt,
            "at": step.at.isoformat(),
        },
        document_id=document_id,
    )


def processing_failed(session: Session, document_id: UUID, error: BaseException) -> None:
    """Vetëm lloji i gabimit. Mesazhi mund të mbajë të dhëna — gabimet e
    validimit të Pydantic-ut përfshijnë vlerat hyrëse — dhe mbetet te rreshti
    i punës, që i përket pronarit të dokumentit."""
    _record(
        session,
        "processing.failed",
        {"error_type": type(error).__name__},
        document_id=document_id,
    )


def document_deleted(session: Session, document_id: UUID, user_id: UUID) -> None:
    _record(session, "document.deleted", {}, document_id=document_id, user_id=user_id)
