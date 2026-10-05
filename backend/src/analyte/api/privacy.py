"""
Mbrojtja e të dhënave: çfarë ofron shërbimi, eksporti i të dhënave tuaja dhe fshirja e llogarisë (ADR 0019).

  - `GET /privacy/config` — çfarë dërgohet jashtë sistemit dhe sa ruhet. I hapur, sepse faqja e ngarkimit duhet ta dijë
    para se të pyesë për pëlqim; kthen vetëm vlera të pakta (a është modeli i ndezur, kush është ofruesi, sa ditë ruhet).
  - `GET /me/export` — të dhënat e llogarisë dhe të dokumenteve të pronarit, si JSON. Asgjë të një përdoruesi tjetër,
    asnjë hash fjalëkalimi, asnjë token, asnjë tekst i koduar.
  - `DELETE /me/data` — fshin llogarinë dhe gjithçka të lidhur me të. Kërkon fjalëkalimin aktual në trup: një token
    aksesi i vjedhur nuk duhet të mjaftojë për të fshirë një llogari. Provat e gabuara numërohen te kovat e hyrjes
    (`throttle`), që kjo pikë të mos bëhet një rrugë tjetër për të provuar fjalëkalimin.

Fshirja e një dokumenti të vetëm është te `documents.py` (`DELETE /documents/{id}`); të dyja kalojnë nga
`erasure`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from analyte.audit import logger as audit
from analyte.config import Settings
from analyte import erasure
from analyte.persistence.tables import (
    AssertionRow,
    AuditEventRow,
    DocumentRow,
    ExplanationRow,
    FindingRow,
    UserRow,
)
from analyte.security import verify_password

from . import deps, throttle
from .problems import Problem

router = APIRouter(tags=["privacy"])


class PrivacyConfig(BaseModel):
    model_enabled: bool
    """Shërbimi gjeneron me një model gjuhësor të jashtëm (`ANALYTE_SERVICE_GENERATOR=model`). Vetëm atëherë faqja e
    ngarkimit pyet për pëlqim."""
    model_provider: str | None
    """Ofruesi si është i konfiguruar (`mistral`, `gemini`…), që pacienti të dijë kujt i dërgohet; None kur modeli është i fikur."""
    retention_days: int
    """Sa ditë ruhet një dokument; 0 = derisa pronari ta fshijë."""


@router.get("/privacy/config", response_model=PrivacyConfig)
def privacy_config(config: Settings = Depends(deps.settings)) -> PrivacyConfig:
    enabled = config.service_generator == "model"
    return PrivacyConfig(
        model_enabled=enabled,
        model_provider=(config.llm_provider or None) if enabled else None,
        retention_days=config.document_retention_days,
    )


class ErasureIn(BaseModel):
    password: str = Field(min_length=1, max_length=256)


@router.delete("/me/data", status_code=204)
def erase_account(
    body: ErasureIn,
    request: Request,
    user: UserRow = Depends(deps.current_user),
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> Response:
    """Fshin llogarinë dhe çdo dokument të saj, pas verifikimit të fjalëkalimit.

    Pas kësaj tokenët e pronarit nuk vlejnë më (seancat shkojnë me llogarinë), prandaj një përsëritje e së njëjtës kërkesë
    kthen 401, jo një gabim tjetër. Fjalëkalimi i gabuar kthen 403 dhe jo 401, që klienti të mos e marrë për seancë të
    skaduar dhe të nisë një rifreskim.
    """
    now = datetime.now(UTC)
    keys = throttle.keys_for(
        user.email,
        throttle.client_ip(request, config.trusted_proxy_hops, config.ipv6_prefix_bits),
        config,
    )
    throttle.check(db, config, keys, now)
    if not verify_password(user.password_hash, body.password):
        throttle.record_failure(db, config, keys, now)
        raise Problem(403, "Fjalëkalimi nuk përputhet")

    erasure.erase_user(db, request.app.state.store, user, config)
    db.commit()  # para përgjigjes: kur klienti merr 204, të dhënat janë fshirë
    return Response(status_code=204)


def _exact(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def build_export(db: Session, request: Request, user: UserRow) -> dict[str, Any]:
    """Të dhënat e një përdoruesi, të kapura nga pronësia: çdo pyetje filtrohet me `user_id` ose me dokumentet e tij."""
    store = request.app.state.store
    documents = db.scalars(
        select(DocumentRow).where(DocumentRow.user_id == user.id).order_by(DocumentRow.uploaded_at)
    ).all()
    ids = [document.id for document in documents]

    exported: list[dict[str, Any]] = []
    for document in documents:
        findings = db.scalars(
            select(FindingRow).where(FindingRow.document_id == document.id).order_by(FindingRow.position)
        ).all()
        assertions = db.scalars(
            select(AssertionRow).where(AssertionRow.document_id == document.id).order_by(AssertionRow.position)
        ).all()
        attempts = db.scalars(
            select(ExplanationRow)
            .where(ExplanationRow.document_id == document.id)
            .order_by(ExplanationRow.attempt)
        ).all()
        delivered = next((a for a in attempts if a.delivered), None)
        exported.append(
            {
                "id": document.id,
                "filename": store.decrypt_text(document.filename_encrypted),
                "uploaded_at": document.uploaded_at,
                "mime": document.mime,
                "size_bytes": document.size_bytes,
                "sha256": document.sha256,
                "state": document.state,
                "state_reason": document.state_reason,
                "channel": document.channel,
                "model": {
                    "consent": document.model_consent,
                    "consent_at": document.model_consent_at,
                    "use": document.model_use,
                    "gate_kinds": [k for k in (document.model_gate_kinds or "").split(",") if k],
                },
                "findings": [
                    {
                        "analyte_code": f.analyte_code,
                        "analyte_name_raw": f.analyte_name_raw,
                        "analyte_name_canonical": f.analyte_name_canonical,
                        "value_raw": f.value_raw,
                        "value": _exact(f.value),
                        "unit_raw": f.unit_raw,
                        "unit_canonical": f.unit_canonical,
                        "value_canonical": _exact(f.value_canonical),
                        "ref_low": _exact(f.ref_low),
                        "ref_high": _exact(f.ref_high),
                        "ref_source": f.ref_source,
                        "status": f.status,
                        "page": f.page,
                        "measured_at": f.measured_at,
                        "flag_in_document": f.flag_in_document,
                    }
                    for f in findings
                ],
                "assertions": [
                    {
                        "text_span": a.text_span,
                        "kind": a.kind,
                        "direction": a.direction,
                        "polarity": a.polarity,
                        "certainty": a.certainty,
                    }
                    for a in assertions
                ],
                "explanation": (
                    {
                        "text": delivered.final_output,
                        "generator": delivered.generator,
                        "is_fallback": delivered.is_fallback,
                    }
                    if delivered
                    else None
                ),
                "attempts": [
                    {
                        "attempt": a.attempt,
                        "generator": a.generator,
                        "is_fallback": a.is_fallback,
                        "delivered": a.delivered,
                        "raw_output": a.raw_output,
                        "error": a.error,
                    }
                    for a in attempts
                ],
            }
        )

    conditions = [AuditEventRow.user_id == user.id]
    if ids:
        conditions.append(AuditEventRow.document_id.in_(ids))
    events = db.scalars(select(AuditEventRow).where(or_(*conditions)).order_by(AuditEventRow.id)).all()

    return {
        "exported_at": datetime.now(UTC),
        "account": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
            "email_confirmed_at": user.email_confirmed_at,
        },
        "documents": exported,
        "audit_events": [
            {
                "event_type": e.event_type,
                "created_at": e.created_at,
                "document_id": e.document_id,
                "payload": e.payload,
            }
            for e in events
        ],
        "notes": [
            "Skedari PDF origjinal nuk përfshihet në këtë eksport: e keni ngarkuar ju.",
            "Hash-et e fjalëkalimit, tokenët dhe seancat nuk përfshihen kurrë.",
        ],
    }


@router.get("/me/export")
def export(
    request: Request,
    user: UserRow = Depends(deps.current_user),
    db: Session = Depends(deps.session),
) -> JSONResponse:
    data = build_export(db, request, user)
    audit.user_exported(db, user.id)
    return JSONResponse(
        jsonable_encoder(data),
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'attachment; filename="analyte-eksport.json"',
        },
    )
