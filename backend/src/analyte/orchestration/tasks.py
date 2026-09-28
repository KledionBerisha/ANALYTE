"""
Puna e përpunimit të një dokumenti, dhe mënyrat si nis ajo.

`run_document` e merr dokumentin nga baza, e dekodon në një skedar të
përkohshëm, e drejton përmes makinës së gjendjeve dhe e shkruan rezultatin.
Ajo nuk di nëse u thirr nga radha e punëve apo drejtpërdrejt: `InlineRunner`
e thërret brenda kërkesës (teste, prova), `ArqRunner` e dërgon te radha dhe
kërkesa kthehet menjëherë (NFR4).

**Kalimet shkruhen ndërsa ndodhin**, secili në transaksionin e vet, që
`/status` të tregojë "ocr_running" gjatë OCR-së dhe jo vetëm në fund.

**Gjendja përfundimtare shkruhet bashkë me rezultatet**, në një transaksion
të vetëm. Përndryshe një klient që pyet në çastin e gabuar do të shihte
"delivered" para se shpjegimi të ekzistonte në bazë.

**Gabimi i papritur nuk e fsheh dokumentin.** Nëse përpunimi ngrihet — një
defekt, jo një gjendje e dokumentit — puna shënohet me gabim dhe dokumenti
mbetet në gjendjen e fundit të arritur. Gabimi i verifikuesit nuk kthehet
në shabllon të dorëzuar (ADR 0011); ai duket.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from analyte.audit import logger as audit
from analyte.generation.base import Generator
from analyte.persistence import repository
from analyte.persistence.database import session_scope
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import DocumentRow, JobRow

from .process import Ocr, process
from .states import StateLog, Transition


@dataclass(frozen=True)
class Services:
    """Gjithçka që i duhet punës, e ndërtuar një herë për proces."""

    sessions: sessionmaker[Session]
    store: EncryptedStore
    generator: Generator
    ocr: Ocr | None = None


def _now() -> datetime:
    return datetime.now(UTC)


def _latest_job(session: Session, document_id: UUID) -> JobRow:
    return session.scalars(
        select(JobRow).where(JobRow.document_id == document_id).order_by(JobRow.created_at.desc())
    ).first()


def _apply(session: Session, document_id: UUID, step: Transition) -> None:
    document = session.get(DocumentRow, document_id)
    document.state = step.target.value
    document.state_reason = step.reason
    job = _latest_job(session, document_id)
    job.state = step.target.value
    job.attempt = step.attempt if step.attempt is not None else job.attempt
    audit.transition(session, document_id, step)


def run_document(services: Services, document_id: UUID) -> None:
    with session_scope(services.sessions) as session:
        document = session.get(DocumentRow, document_id)
        if document is None:
            return  # u fshi para se puna të nisej
        storage_path = document.storage_path
        _latest_job(session, document_id).started_at = _now()

    terminal: list[Transition] = []

    def on_transition(step: Transition) -> None:
        if step.target.is_terminal:
            terminal.append(step)
            return
        with session_scope(services.sessions) as session:
            if session.get(DocumentRow, document_id) is not None:
                _apply(session, document_id, step)

    try:
        with services.store.decrypted(storage_path) as path:
            outcome = process(
                document_id,
                path,
                services.generator,
                ocr=services.ocr,
                log=StateLog(listener=on_transition),
            )
    except Exception as error:
        with session_scope(services.sessions) as session:
            if session.get(DocumentRow, document_id) is None:
                return
            job = _latest_job(session, document_id)
            job.error = f"{type(error).__name__}: {error}"
            job.finished_at = _now()
            audit.processing_failed(session, document_id, error)
        return

    with session_scope(services.sessions) as session:
        document = session.get(DocumentRow, document_id)
        if document is None:
            return
        document.channel = outcome.channel.value if outcome.channel else None
        if outcome.context is not None:
            repository.save_context(session, outcome.context)
        if outcome.explanation is not None:
            repository.save_explanation(session, document_id, outcome.explanation)
        for step in terminal:
            _apply(session, document_id, step)
        _latest_job(session, document_id).finished_at = _now()


class JobRunner(Protocol):
    def submit(self, document_id: UUID) -> None: ...


class InlineRunner:
    """Përpunon brenda kërkesës. Vetëm për teste dhe prova lokale."""

    def __init__(self, services: Services) -> None:
        self.services = services

    def submit(self, document_id: UUID) -> None:
        run_document(self.services, document_id)


class ArqRunner:
    """Dërgon punën te radha; punëtori (`orchestration.worker`) e kryen."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url

    def submit(self, document_id: UUID) -> None:
        asyncio.run(self._enqueue(str(document_id)))

    async def _enqueue(self, document_id: str) -> None:
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(RedisSettings.from_dsn(self.redis_url))
        try:
            await pool.enqueue_job("run_document_job", document_id)
        finally:
            await pool.aclose()


def build_services(settings: Any) -> Services:
    """Shërbimet nga konfigurimi — i njëjti ndërtim për API-në dhe punëtorin."""
    from analyte.generation.templates import TemplateGenerator
    from analyte.persistence.database import make_engine, make_session_factory

    ocr = None
    if settings.ocr:
        from analyte.ingestion.ocr import OcrUnavailable, TesseractOcr

        try:
            ocr = TesseractOcr()
        except OcrUnavailable:
            ocr = None  # dokumentet e skanuara përfundojnë në FAILED_INGESTION me arsye

    return Services(
        sessions=make_session_factory(make_engine(settings.database_url)),
        store=EncryptedStore(settings.storage_dir, settings.storage_key),
        # Modeli gjuhësor mungon ende (vendim i autorit, 2026-09-27); shablloni
        # determinist është gjeneruesi, dhe emri i tij ruhet me çdo përpjekje.
        generator=TemplateGenerator(),
        ocr=ocr,
    )
