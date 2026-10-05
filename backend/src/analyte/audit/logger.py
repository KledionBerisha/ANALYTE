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

from analyte.domain.processing import Transition
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


def email_confirmed(session: Session, user_id: UUID) -> None:
    _record(session, "user.email_confirmed", {}, user_id=user_id)


def mail_failed(session: Session, error_type: str) -> None:
    """Vetëm lloji i gabimit të dërgimit. As adresa, as lidhja: log-u i auditimit nuk i mban (NFR5)."""
    _record(session, "mail.failed", {"error_type": error_type})


def mail_reissued(session: Session, user_id: UUID, kind: str) -> None:
    """Kalimi periodik lëshoi një token të ri sepse mesazhi i mëparshëm nuk u dërgua (ADR 0018). Vetëm lloji
    (`confirmation` ose `password_reset`), pa adresë dhe pa lidhje."""
    _record(session, "mail.reissued", {"kind": kind}, user_id=user_id)


def password_reset(session: Session, user_id: UUID) -> None:
    _record(session, "auth.password_reset", {}, user_id=user_id)


def two_factor_enabled(session: Session, user_id: UUID) -> None:
    _record(session, "auth.two_factor_enabled", {}, user_id=user_id)


def two_factor_disabled(session: Session, user_id: UUID) -> None:
    _record(session, "auth.two_factor_disabled", {}, user_id=user_id)


def recovery_code_used(session: Session, user_id: UUID, remaining: int) -> None:
    """Një kod rimëkëmbjes u shpenzua; `remaining` që ndërfaqja ta paralajmërojë kur mbeten pak."""
    _record(session, "auth.recovery_code_used", {"remaining": remaining}, user_id=user_id)


def sessions_revoked_all(session: Session, user_id: UUID, count: int) -> None:
    _record(session, "auth.sessions_revoked_all", {"count": count}, user_id=user_id)


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


def model_consent_recorded(session: Session, document_id: UUID, user_id: UUID, given: bool) -> None:
    """Pëlqimi (ose mospëlqimi) për dërgimin te ofruesi i modelit, për këtë ngarkim (ADR 0019). Vetëm një
    e vërtetë/gënjeshtër: asnjë përmbajtje dokumenti."""
    _record(
        session,
        "document.model_consent",
        {"given": given},
        document_id=document_id,
        user_id=user_id,
    )


def model_use_decided(
    session: Session, document_id: UUID, use: str, kinds: tuple[str, ...] = ()
) -> None:
    """Çfarë ndodhi me modelin për një dokument: `used`, `no_consent` ose `identifying_content`. `kinds` janë
    kodet e llojeve që gjeti porta e çidentifikimit (`name_like`, `date`…), kurrë vargjet e gjetura."""
    _record(
        session,
        "document.model_use",
        {"use": use, "kinds": list(kinds)},
        document_id=document_id,
    )


def document_expired(session: Session, document_id: UUID, user_id: UUID, retention_days: int) -> None:
    """Dokumenti u fshi sepse kaloi afatin e ruajtjes (`ANALYTE_DOCUMENT_RETENTION_DAYS`)."""
    _record(
        session,
        "document.expired",
        {"retention_days": retention_days},
        document_id=document_id,
        user_id=user_id,
    )


def user_erased(session: Session, documents: int) -> None:
    """Llogaria u fshi me kërkesë të pronarit. Pa identifikuesin e përdoruesit: pas fshirjes ai nuk lidhet më me
    asgjë, dhe ngjarja thotë vetëm sa dokumente u hoqën."""
    _record(session, "user.erased", {"documents": documents})


def user_exported(session: Session, user_id: UUID) -> None:
    _record(session, "user.exported", {}, user_id=user_id)
