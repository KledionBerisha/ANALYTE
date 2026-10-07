"""
Puna e përpunimit të një dokumenti, dhe mënyrat si nis ajo.

"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from analyte.audit import logger as audit
from analyte.generation.base import Generator
from analyte.persistence import repository
from analyte.persistence.database import session_scope
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import DocumentRow, JobRow

from . import model_gate
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
        consent = document.model_consent
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
                choose=model_gate.chooser(services.generator, consent),
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

    try:
        with session_scope(services.sessions) as session:
            document = session.get(DocumentRow, document_id)
            if document is None:
                return
            document.channel = outcome.channel.value if outcome.channel else None
            if outcome.model_use is not None:
                document.model_use = outcome.model_use
                document.model_gate_kinds = ",".join(outcome.model_gate_kinds) or None
                audit.model_use_decided(
                    session, document_id, outcome.model_use, outcome.model_gate_kinds
                )
            if outcome.context is not None:
                repository.save_context(session, outcome.context)
            if outcome.explanation is not None:
                repository.save_explanation(session, document_id, outcome.explanation)
            for step in terminal:
                _apply(session, document_id, step)
            _latest_job(session, document_id).finished_at = _now()
    except IntegrityError:
        # Pronari e fshiu dokumentin (ose afati i ruajtjes e fshiu) pikërisht ndërsa rezultatet po shkruheshin: çelësi
        # i huaj refuzon rreshtat e rinj dhe transaksioni kthehet prapa. Nuk ka asgjë për t'u ruajtur; çdo gjë tjetër
        # është defekt dhe ngrihet (ADR 0019).
        with session_scope(services.sessions) as session:
            if session.get(DocumentRow, document_id) is None:
                return
        raise


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


def build_generator(settings: Any):
    """Gjeneruesi i aplikacionit: shablloni determinist, ose modeli gjuhësor kur `ANALYTE_SERVICE_GENERATOR=model` (ADR 0017).

    **Modeli është zgjedhje e shprehur, jo parazgjedhje.** Me `template` (parazgjedhja), edhe nëse `.env` ka ofruesin për
    eksperimentet, shpjegimi del nga shablloni dhe asnjë e dhënë nuk del nga sistemi. Me `model`, konteksti i strukturuar (vlera laboratorike, statuse, citime të mjekut; kurrë emri, mosha, gjinia
    apo dokumenti i papërpunuar) i dërgohet ofruesit **vetëm për dokumentet me pëlqim të shprehur të pacientit që kalojnë
    portën e çidentifikimit** (ADR 0019, `model_gate`); të tjerët dalin me shabllon. Kjo duhet të jetë vendim i mirëmenduar (docs/ethics).

    **Pa cache në disk.** Harness-i i vlerësimit i ruan përgjigjet e modelit te depoja (`evaluation/cache/llm`), që eksperimentet
    të përsëriten; këtu kërkesat dhe përgjigjet përmbajnë të dhëna të pacientëve të vërtetë, dhe asnjë kopje e tyre nuk shkruhet
    në disk. Klienti ndërtohet pa `cache_dir`.

    `model` pa ofrues, model ose çelës (konfigurim i paplotë) hedh `ProviderError` kur shërbimi nis, jo gjatë një dokumenti.
    """
    from analyte.generation.templates import TemplateGenerator

    if getattr(settings, "service_generator", "template") != "model":
        return TemplateGenerator()
    from analyte.generation.llm import LlmGenerator, build_client

    return LlmGenerator(build_client(settings))


def build_services(settings: Any) -> Services:
    """Shërbimet nga konfigurimi — i njëjti ndërtim për API-në dhe punëtorin."""
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
        generator=build_generator(settings),
        ocr=ocr,
    )
