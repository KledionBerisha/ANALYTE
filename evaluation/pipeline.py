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
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

from analyte.domain.enums import ProcessingState
from analyte.domain.models import GroundingContext, VerificationResult, Violation
from analyte.domain.policy import LEGACY_RULES_VERSION

if TYPE_CHECKING:
    from analyte.generation.base import Generator
    from analyte.orchestration.process import Attempt


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
    attempts: tuple[Attempt, ...] = ()
    """Çdo përpjekje e gjeneruesit, kur kushti rigjeneron (E8, E9).

    Pa to, PK5 do të shihte vetëm tekstin e fundit të modelit dhe shkeljet
    e përpjekjes së parë — ato që verifikimi i ndali — do të zhdukeshin nga
    numri i shkeljeve të prodhuara."""
    delivered_verification: VerificationResult | None = None
    """Verifikimi i tekstit që mori përdoruesi, kur ai ndryshon nga
    `explanation` — p.sh. shablloni pas dy dështimeve."""

    @property
    def delivered(self) -> bool:
        """A do t'i kishte shkuar ky tekst përdoruesit?

        NFR1: vetëm teksti që kalon verifikimin shfaqet. Kushtet pa
        verifikim (E6, E7) japin gjithçka, dhe pikërisht ky dallim është
        ajo që mat ablacioni.
        """
        return self.state is ProcessingState.DELIVERED

    def drafts(self) -> tuple[tuple[str, VerificationResult | None], ...]:
        """Tekstet që prodhoi gjeneruesi, secili me verifikimin e vet."""
        if self.attempts:
            return tuple((a.text, a.verification) for a in self.attempts if a.text is not None)
        return ((self.explanation, self.verification),) if self.explanation else ()

    def violations_reaching_user(self) -> tuple[Violation, ...]:
        """Shkeljet në tekstin që mori përdoruesi."""
        if self.attempts:
            verification = self.delivered_verification
            return verification.violations if verification else ()
        if not self.delivered or self.verification is None:
            return ()
        return self.verification.violations


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


def _read_pages(document: DocumentInput, ocr) -> tuple[tuple, str | None]:
    """Faqet e dokumentit, ose arsyeja pse nuk u lexuan.

    Pa OCR, dokumenti i skanuar kthehet si i palexuar dhe jo si bosh:
    "nuk u lexua dot" dhe "nuk kishte asgjë brenda" janë gjendje të
    ndryshme (Figura 6), dhe PK1 i të skanuarave duhet ta tregojë këtë.
    """
    from analyte.ingestion.router import route

    routing = route(document.pdf_path)
    if routing.has_text:
        return routing.pages, None
    if ocr is None:
        return (), routing.reason
    try:
        return ocr(document.pdf_path), None
    except Exception as error:
        return (), f"OCR dështoi: {type(error).__name__}: {error}"


@dataclass(frozen=True, slots=True)
class BranchAPipeline:
    """Dega A e vërtetë: lexim i PDF-së, nxjerrje, klasifikim.

    Nuk gjeneron tekst dhe nuk verifikon asgjë — ajo është Faza 6.
    Prandaj E4 dhe E6-E9 mbeten të pamatura edhe me këtë pipeline, dhe
    kjo duhet të duket si `n/a` e jo si zero.

    Dokumentet pa shtresë teksti lexohen me `ocr` kur jepet; përndryshe
    kthehen si FAILED_INGESTION.
    """

    name: str = "branch_a"
    version: str = "1"
    ocr: Any = None
    ocr_guard: bool = False
    """Kontrolli i besueshmërisë i OCR-së (ADR 0020). I fikur te eksperimentet e ngrira."""

    def run(self, document: DocumentInput) -> PipelineOutput:
        from analyte.grounding.branch_a.extract import extract

        pages, failure = _read_pages(document, self.ocr)
        if failure is not None:
            return PipelineOutput(
                context=GroundingContext(document_id=document.document_id),
                state=ProcessingState.FAILED_INGESTION,
                failures=(failure,),
            )

        result = extract(pages, ocr_guard=self.ocr_guard)
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
    ocr: Any = None
    ocr_guard: bool = False
    """Kontrolli i besueshmërisë i OCR-së (ADR 0020). I fikur te eksperimentet e ngrira."""

    def run(self, document: DocumentInput) -> PipelineOutput:
        from analyte.grounding.context import build

        pages, failure = _read_pages(document, self.ocr)
        if failure is not None:
            return PipelineOutput(
                context=GroundingContext(document_id=document.document_id),
                state=ProcessingState.FAILED_INGESTION,
                failures=(failure,),
            )

        grounding = build(document.document_id, pages, ocr_guard=self.ocr_guard)
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


ABLATIONS = ("E6", "E7", "E8", "E9")
"""Kushtet e ablacionit. Secili është pipeline më vete, dhe harness-i nuk
lejon që rezultati i njërit të regjistrohet nën ID-në e një tjetri."""


@dataclass(frozen=True, slots=True)
class GenerationPipeline:
    """Bazimi i plotë, pastaj gjenerimi — kushtet E7, E8 dhe E9.

    **E7 (vetëm bazim).** Një përpjekje; teksti verifikohet që shkeljet të
    numërohen, por dorëzohet pavarësisht tyre.

    **E8 (+ verifikim me rregulla).** Cikli i plotë i `explain`: rigjenerim
    me shkeljet në kërkesë dhe shabllon pas dy dështimeve. Teksti në
    `explanation` është drafti i fundit i modelit — ai që mat PK3 — dhe jo
    domosdoshmërisht ai që mori përdoruesi.

    **E9 (+ klasifikues).** I njëjti cikël si E8, me verifikues që ekzekuton
    rregullat dhe pastaj klasifikuesin mbi fjalitë që ato lanë të pastra
    (ADR 0009). Pragu vjen nga E11, ku u zgjodh vetëm mbi validimin.

    **E6 nuk zbatohet këtu.** Ai kërkon një gjenerues që sheh dokumentin e
    papërpunuar, gjë që protokolli `Generator` e ndalon me qëllim.

    Dokumentet që nuk bazohen — të skanuarat pa OCR, ato pa gjetje — nuk
    arrijnë te gjenerimi dhe dalin me gjendjen e bazimit.
    """

    generator: Generator
    ablation: str = "E8"
    version: str = "1"
    ocr: Any = None
    ocr_guard: bool = False
    rules: str = LEGACY_RULES_VERSION
    """Versioni i katalogut me të cilin verifikohet (r1.3 e ngrirë; shih `verification/ruleset.py`)."""
    classifier: Any = None
    """Parashikuesi i fjalive (`SentencePredictor`), vetëm për E9."""
    threshold: float | None = None

    def __post_init__(self) -> None:
        if self.ablation not in {"E7", "E8", "E9"}:
            raise ValueError(f"kushti {self.ablation} nuk zbatohet nga ky pipeline")
        if (self.ablation == "E9") != (self.classifier is not None):
            raise ValueError("E9 kërkon klasifikues, dhe vetëm E9 e përdor atë")
        if self.classifier is not None and self.threshold is None:
            raise ValueError("klasifikuesi kërkon pragun e zgjedhur te E11")

    @property
    def name(self) -> str:
        suffix = "+ocr" if self.ocr is not None else ""
        suffix += "+guard" if self.ocr_guard else ""
        if self.classifier is not None:
            suffix += f"+{self.classifier.version}@{self.threshold}"
        return f"{self.ablation.lower()}[{self.generator.name}]{suffix}"

    def _verifier(self):
        from analyte.verification.pipeline import verify

        if self.classifier is None:
            return lambda context, text: verify(context, text, rules=self.rules)
        from analyte.verification.classifier import verify_with_classifier

        return lambda context, text: verify_with_classifier(
            context, text, self.classifier, self.threshold, rules=self.rules
        )

    def run(self, document: DocumentInput) -> PipelineOutput:
        from analyte.orchestration.process import Attempt, Delivery, explain
        from analyte.verification.pipeline import verify

        grounded = GroundingPipeline(ocr=self.ocr, ocr_guard=self.ocr_guard).run(document)
        if grounded.state is not ProcessingState.GROUNDED:
            return grounded
        context = grounded.context

        if self.ablation == "E7":
            try:
                text = self.generator(context, ())
            except Exception as error:
                return PipelineOutput(
                    context=context,
                    state=ProcessingState.GROUNDED,
                    failures=(f"{type(error).__name__}: {error}",),
                )
            verification = verify(context, text, rules=self.rules)
            return PipelineOutput(
                context=context,
                explanation=text,
                verification=verification,
                attempts=(Attempt(1, self.generator.name, text, verification),),
                delivered_verification=verification,
                failures=grounded.failures,
            )

        explanation = explain(context, self.generator, verifier=self._verifier())
        drafts = [a for a in explanation.attempts if a.text is not None]
        last = drafts[-1] if drafts else None
        return PipelineOutput(
            context=context,
            explanation=last.text if last else "",
            verification=last.verification if last else None,
            state=(
                ProcessingState.DELIVERED
                if explanation.delivery is Delivery.GENERATED
                else ProcessingState.TEMPLATE_FALLBACK
            ),
            attempts=explanation.attempts,
            delivered_verification=explanation.verification,
            failures=grounded.failures
            + tuple(f"përpjekja {a.number}: {a.error}" for a in explanation.attempts if a.error),
        )
