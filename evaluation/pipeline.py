"""
Ç'është një "sistem" për vlerësimin.

Vlerësimi nuk njeh shtresa: ai njeh diçka që merr një dokument dhe kthen
atë që sistemi mendon për të. Kjo ndarje e lejon harness-in të ekzistojë
para se të ekzistojë ndonjë shtresë e vërtetë, dhe i mban kushtet e
ablacionit (§8, E6-E9) si zbatime të ndryshme të së njëjtës ndërfaqe në
vend që si degë `if` brenda kodit të prodhimit.

**Kufiri.** `DocumentInput` përmban vetëm atë që sistemi ka të drejtë të
shohë: identifikuesin dhe shtegun e PDF-së. E vërteta bazë nuk kalon
kurrë prej këtej. Kjo nuk është konventë por kusht i vlefshmërisë së çdo
numri që del nga harness-i, prandaj ka test të vetin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from uuid import UUID

from analyte.domain.enums import ProcessingState
from analyte.domain.models import GroundingContext, VerificationResult


@dataclass(frozen=True, slots=True)
class DocumentInput:
    """Dokumenti ashtu si i jepet sistemit: një skedar dhe asgjë më shumë."""

    document_id: UUID
    pdf_path: Path


@dataclass(frozen=True, slots=True)
class PipelineOutput:
    """Çfarë prodhoi sistemi për një dokument.

    `context` është konteksti i nxjerrë — ai që krahasohet me të vërtetën
    bazë te PK1, PK2 dhe PK4. `explanation` është teksti që do t'i
    shfaqej përdoruesit, dhe `verification` vendimi për të; të dyja
    mungojnë te kushtet që nuk gjenerojnë fare.
    """

    context: GroundingContext
    explanation: str = ""
    verification: VerificationResult | None = None
    state: ProcessingState = ProcessingState.DELIVERED
    failures: tuple[str, ...] = field(default=())

    @property
    def delivered(self) -> bool:
        """A do t'i kishte shkuar ky tekst përdoruesit?

        NFR1: vetëm teksti që kalon verifikimin shfaqet. Kushtet pa
        verifikim (E6, E7) japin gjithçka, dhe pikërisht ky dallim është
        ajo që mat ablacioni.
        """
        return self.state is ProcessingState.DELIVERED


class Pipeline(Protocol):
    """Ndërfaqja që çdo kusht eksperimenti duhet të plotësojë."""

    name: str
    version: str

    def run(self, document: DocumentInput) -> PipelineOutput:
        ...


@dataclass(frozen=True, slots=True)
class EmptyPipeline:
    """Sistemi që nuk nxjerr asgjë.

    Kjo është kufiri i poshtëm i çdo metrike dhe pipeline-i me të cilin
    harness-i u provua para se të ekzistonte ndonjë shtresë: ai prodhon
    tabelë të plotë rezultatesh me zero kudo. Një metrikë që dështon mbi
    të — që pjesëton me zero ose që kthen 1.0 — është e prishur.
    """

    name: str = "empty"
    version: str = "0"

    def run(self, document: DocumentInput) -> PipelineOutput:
        return PipelineOutput(
            context=GroundingContext(document_id=document.document_id),
            state=ProcessingState.NO_FINDINGS,
        )


@dataclass(frozen=True, slots=True)
class OraclePipeline:
    """Sistemi që di gjithçka.

    Nuk është sistem: është provë e metrikave. Një metrikë që nuk arrin
    vlerën e përsosur mbi orakullin ka gabim në vetvete, dhe pa këtë
    kontroll ai gabim do të dukej si dobësi e sistemit të matur.

    Prandaj orakulli merr të vërtetën në ndërtues dhe jo nga
    `DocumentInput`: kufiri mbetet i paprekur edhe këtu, dhe asnjë
    pipeline tjetër nuk ka nga ku ta marrë atë.
    """

    truth: dict[UUID, GroundingContext]
    name: str = "oracle"
    version: str = "0"

    def run(self, document: DocumentInput) -> PipelineOutput:
        return PipelineOutput(context=self.truth[document.document_id])


@dataclass(frozen=True, slots=True)
class BranchAPipeline:
    """Dega A e vërtetë: lexim i PDF-së, nxjerrje, klasifikim.

    Nuk gjeneron tekst dhe nuk verifikon asgjë — ajo është Faza 6.
    Prandaj E4 dhe E6-E9 mbeten të pamatura edhe me këtë pipeline, dhe
    kjo duhet të duket si `n/a` e jo si zero.

    Dokumentet pa shtresë teksti nuk përpunohen: rruga e OCR-së ende nuk
    ekziston. Ato kthehen si FAILED_INGESTION dhe jo si dokumente bosh,
    sepse "nuk u lexua dot" dhe "nuk kishte asgjë brenda" janë gjendje të
    ndryshme (Figura 6) dhe PK1 i të skanuarave duhet ta tregojë këtë
    ndryshim.
    """

    name: str = "branch_a"
    version: str = "1"

    def run(self, document: DocumentInput) -> PipelineOutput:
        from analyte.grounding.branch_a.extract import extract
        from analyte.ingestion.router import route

        routing = route(document.pdf_path)
        if not routing.has_text:
            return PipelineOutput(
                context=GroundingContext(document_id=document.document_id),
                state=ProcessingState.FAILED_INGESTION,
                failures=(routing.reason,),
            )

        result = extract(routing.pages)
        context = GroundingContext(
            document_id=document.document_id, findings=result.findings
        )
        return PipelineOutput(
            context=context,
            state=(
                ProcessingState.GROUNDED
                if result.findings
                else ProcessingState.NO_FINDINGS
            ),
            failures=tuple(f"{name}: {motive}" for name, motive in result.rejected),
        )


@dataclass(frozen=True, slots=True)
class GroundingPipeline:
    """Të dyja degët: vlerat nga tabela dhe pohimet nga narrativa.

    Ky është sistemi i plotë i bazimit — gjithçka që i jepet modelit
    gjuhësor kur ai të ekzistojë. Gjenerimi dhe verifikimi janë Faza 6,
    prandaj E4 dhe E6-E9 mbeten `n/a` edhe këtu.
    """

    name: str = "grounding"
    version: str = "1"

    def run(self, document: DocumentInput) -> PipelineOutput:
        from analyte.grounding.context import build
        from analyte.ingestion.router import route

        routing = route(document.pdf_path)
        if not routing.has_text:
            return PipelineOutput(
                context=GroundingContext(document_id=document.document_id),
                state=ProcessingState.FAILED_INGESTION,
                failures=(routing.reason,),
            )

        grounding = build(document.document_id, routing.pages)
        return PipelineOutput(
            context=grounding.context,
            state=(
                ProcessingState.GROUNDED
                if grounding.has_content
                else ProcessingState.NO_FINDINGS
            ),
            failures=tuple(
                f"{name}: {motive}" for name, motive in grounding.extraction.rejected
            ),
        )
