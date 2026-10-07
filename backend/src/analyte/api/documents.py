"""
Dokumentet: ngarkimi, lista, gjendja, fshirja.

"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from analyte import erasure
from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.domain.enums import ProcessingState
from analyte.persistence.tables import AuditEventRow, DocumentRow, JobRow, UserRow

from . import deps
from .problems import Problem
from .schemas import (
    DocumentOut,
    DocumentPage,
    JobOut,
    StatusOut,
    TransitionOut,
    UploadOut,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _out(request: Request, document: DocumentRow) -> DocumentOut:
    store = request.app.state.store
    return DocumentOut(
        id=document.id,
        filename=store.decrypt_text(document.filename_encrypted),
        uploaded_at=document.uploaded_at,
        size_bytes=document.size_bytes,
        state=document.state,
        state_reason=document.state_reason,
        channel=document.channel,
        terminal=ProcessingState(document.state).is_terminal,
        model_consent=document.model_consent,
    )


@router.post("", response_model=UploadOut, status_code=202)
def upload(
    request: Request,
    file: UploadFile = File(...),
    model_consent: bool = Form(False),
    user: UserRow = Depends(deps.current_user),
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> UploadOut:
    limit = config.max_upload_mb * 1024 * 1024
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise Problem(413, "Skedari është shumë i madh", f"kufiri është {config.max_upload_mb} MB")
    if not content:
        raise Problem(422, "Skedari është bosh")

    store = request.app.state.store
    digest = hashlib.sha256(content).hexdigest()
    # Pëlqimi pyetet vetëm kur shërbimi e ka modelin të ndezur; një klient që dërgon `true` te një shërbim pa model nuk
    # krijon pëlqim për një dërgim që nuk ndodh.
    model_offered = config.service_generator == "model"
    consent = model_offered and model_consent
    now = datetime.now(UTC)
    storage_path = store.put(content)
    document = DocumentRow(
        user_id=user.id,
        filename_encrypted=store.encrypt_text(file.filename or "dokument.pdf"),
        mime=file.content_type or "application/octet-stream",
        sha256=digest,
        size_bytes=len(content),
        storage_path=storage_path,
        state=ProcessingState.UPLOADED.value,
        model_consent=consent,
        model_consent_at=now if consent else None,
    )
    try:
        db.add(document)
        db.flush()
        job = JobRow(document_id=document.id, state=ProcessingState.UPLOADED.value)
        db.add(job)
        audit.document_uploaded(db, document.id, user.id, len(content), digest)
        if model_offered:
            audit.model_consent_recorded(db, document.id, user.id, consent)
        # Puna lexon dokumentin me sesionin e vet; ai duhet të jetë në bazë.
        db.commit()
    except Exception:
        # Skedari u shkrua para rreshtit: pa rresht (p.sh. llogaria u fshi pikërisht tani) nuk do ta fshinte kush.
        db.rollback()
        store.delete(storage_path)
        raise

    try:
        request.app.state.runner.submit(document.id)
    except Exception as error:
        job.error = f"radha e punëve nuk u arrit: {type(error).__name__}"
        db.commit()
        raise Problem(503, "Përpunimi nuk mund të niste", "provoni sërish më vonë") from None

    db.refresh(document)
    return UploadOut(
        id=document.id, job_id=job.id, state=document.state, model_consent=document.model_consent
    )


@router.get("", response_model=DocumentPage)
def history(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    user: UserRow = Depends(deps.current_user),
    db: Session = Depends(deps.session),
) -> DocumentPage:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    mine = select(DocumentRow).where(DocumentRow.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(mine.subquery()))
    rows = db.scalars(
        mine.order_by(DocumentRow.uploaded_at.desc()).limit(limit).offset(offset)
    ).all()
    return DocumentPage(
        items=[_out(request, r) for r in rows], total=total, limit=limit, offset=offset
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get(request: Request, document: DocumentRow = Depends(deps.owned_document)) -> DocumentOut:
    return _out(request, document)


@router.delete("/{document_id}", status_code=204)
def remove(
    request: Request,
    document: DocumentRow = Depends(deps.owned_document),
    db: Session = Depends(deps.session),
) -> Response:
    erasure.erase_documents(db, request.app.state.store, [document])
    db.commit()
    return Response(status_code=204)


@router.get("/{document_id}/status", response_model=StatusOut)
def status(
    document: DocumentRow = Depends(deps.owned_document),
    db: Session = Depends(deps.session),
) -> StatusOut:
    job = db.scalars(
        select(JobRow).where(JobRow.document_id == document.id).order_by(JobRow.created_at.desc())
    ).first()
    events = db.scalars(
        select(AuditEventRow)
        .where(
            AuditEventRow.document_id == document.id,
            AuditEventRow.event_type == "state.transition",
        )
        .order_by(AuditEventRow.id)
    ).all()
    return StatusOut(
        id=document.id,
        state=document.state,
        reason=document.state_reason,
        terminal=ProcessingState(document.state).is_terminal,
        job=(
            JobOut(
                started_at=job.started_at, finished_at=job.finished_at, failed=job.error is not None
            )
            if job
            else None
        ),
        transitions=[
            TransitionOut(
                source=e.payload["from"],
                target=e.payload["to"],
                reason=e.payload["reason"],
                attempt=e.payload["attempt"],
                at=e.payload["at"],
            )
            for e in events
        ],
    )


PAGE_DPI = 110
"""Mjafton për t'u lexuar në ekran; më shumë do të rëndonte çdo kërkesë
pa asnjë fitim për pacientin."""


class PagesOut(BaseModel):
    count: int
    width: float
    height: float
    """Përmasat në pika PDF — njësia e kutive të gjetjeve."""


def _open_pdf(request: Request, document: DocumentRow):
    import pymupdf

    if document.state == ProcessingState.REJECTED.value:
        raise Problem(409, "Skedari nuk është PDF i lexueshëm")
    content = request.app.state.store.get(document.storage_path)
    return pymupdf.open(stream=content, filetype="pdf")


@router.get("/{document_id}/pages", response_model=PagesOut)
def pages(request: Request, document: DocumentRow = Depends(deps.owned_document)) -> PagesOut:
    with _open_pdf(request, document) as pdf:
        first = pdf[0].rect
        return PagesOut(count=pdf.page_count, width=first.width, height=first.height)


@router.get("/{document_id}/pages/{number}", responses={200: {"content": {"image/png": {}}}})
def page_image(
    number: int,
    request: Request,
    document: DocumentRow = Depends(deps.owned_document),
) -> Response:
    with _open_pdf(request, document) as pdf:
        if not 1 <= number <= pdf.page_count:
            raise Problem(404, "Faqja nuk ekziston")
        image = pdf[number - 1].get_pixmap(dpi=PAGE_DPI).tobytes("png")
    return Response(
        image,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300"},
    )
