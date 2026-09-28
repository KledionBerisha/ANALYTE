"""
Dokumentet: ngarkimi, lista, gjendja, fshirja.

**Ngarkimi nuk e gjykon formatin.** Skedari pranohet nëse nuk e kalon
madhësinë, dhe makina e gjendjeve vendos nëse është PDF — degëzimi
UPLOADED → REJECTED i Figurës 6. Një kontroll i dytë këtu do ta linte atë
degë pa u ushtruar kurrë nga shërbimi i vërtetë.

**Fshirja fshin gjithçka përveç gjurmës.** Skedari i koduar, konteksti,
shpjegimet dhe verifikimet shkojnë; ngjarjet e auditimit mbeten, sepse nuk
mbajnë të dhëna shëndetësore dhe janë e vetmja dëshmi se dokumenti u
përpunua dhe u fshi.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

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
    )


@router.post("", response_model=UploadOut, status_code=202)
def upload(
    request: Request,
    file: UploadFile = File(...),
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
    document = DocumentRow(
        user_id=user.id,
        filename_encrypted=store.encrypt_text(file.filename or "dokument.pdf"),
        mime=file.content_type or "application/octet-stream",
        sha256=digest,
        size_bytes=len(content),
        storage_path=store.put(content),
        state=ProcessingState.UPLOADED.value,
    )
    db.add(document)
    db.flush()
    job = JobRow(document_id=document.id, state=ProcessingState.UPLOADED.value)
    db.add(job)
    audit.document_uploaded(db, document.id, user.id, len(content), digest)
    # Puna lexon dokumentin me sesionin e vet; ai duhet të jetë në bazë.
    db.commit()

    try:
        request.app.state.runner.submit(document.id)
    except Exception as error:
        job.error = f"radha e punëve nuk u arrit: {type(error).__name__}"
        db.commit()
        raise Problem(503, "Përpunimi nuk mund të niste", "provoni sërish më vonë") from None

    db.refresh(document)
    return UploadOut(id=document.id, job_id=job.id, state=document.state)


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
    user: UserRow = Depends(deps.current_user),
    db: Session = Depends(deps.session),
) -> Response:
    storage_path, document_id = document.storage_path, document.id
    db.delete(document)
    audit.document_deleted(db, document_id, user.id)
    db.commit()
    request.app.state.store.delete(storage_path)
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
            JobOut(started_at=job.started_at, finished_at=job.finished_at, failed=job.error is not None)
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
