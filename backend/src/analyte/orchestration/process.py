"""
Rruga e plotë e një dokumenti: nga skedari te shpjegimi i dorëzuar.

Moduli ndahet në dy pjesë që mund të thirren veçmas.

`process` e merr dokumentin nga ngarkimi dhe e çon deri në një gjendje
përfundimtare. `explain` fillon nga një kontekst i gatshëm dhe drejton
vetëm ciklin gjenerim → verifikim → rigjenerim → shabllon. Ndarja nuk
është kozmetike: eksperimentet e ablacionit duhet ta drejtojnë ciklin
edhe mbi kontekstin e vërtetë të korpusit, pa kaluar nga nxjerrja, që
gabimet e gjenerimit të maten të ndara nga gabimet e bazimit.

**Asnjë tekst i paverifikuar nuk dorëzohet.** Dalja e gjeneruesit
dorëzohet vetëm pasi verifikimi kalon pa shkelje (NFR1); përndryshe, pas
`MAX_GENERATION_ATTEMPTS` përpjekjesh, dorëzohet shablloni (SP8).

**Shablloni verifikohet gjithashtu.** Rezultati ruhet por nuk e ndal
dorëzimin: shablloni është dalja më e bazuar që sistemi di të prodhojë,
dhe nuk ka rrugë tjetër më të sigurt ku të shkohet. Një shkelje mbi të
është gabim i një rregulli ose i shabllonit, dhe shfaqet në rezultate në
vend që të fshihet.

**Gabimet e verifikuesit dhe të bazimit nuk kapen.** Ato janë defekte të
sistemit, jo gjendje të dokumentit. Kapja e tyre do ta kthente një gabim
programimi në shabllon të dorëzuar pa zhurmë — dhe verifikuesi i prishur
do të mbetej i padukshëm.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from uuid import UUID

from analyte.domain.enums import ProcessingState as S
from analyte.domain.models import GroundingContext, VerificationResult, Violation
from analyte.domain.policy import MAX_GENERATION_ATTEMPTS
from analyte.generation import templates
from analyte.generation.base import Generator
from analyte.grounding.context import build as build_grounding
from analyte.ingestion.format import rejection_reason
from analyte.ingestion.pdf_text import PageText
from analyte.ingestion.router import Channel, route
from analyte.verification.pipeline import verify

from .states import StateLog, Transition

Verifier = Callable[[GroundingContext, str], VerificationResult]
Ocr = Callable[[Path], tuple[PageText, ...]]


class Delivery(str, Enum):
    """Nga erdhi teksti që pa pacienti."""

    GENERATED = "generated"
    TEMPLATE = "template"


@dataclass(frozen=True, slots=True)
class Attempt:
    """Një përpjekje gjenerimi dhe vendimi mbi të.

    Një përpjekje që dështoi me përjashtim nuk ka as tekst as verifikim,
    por ka gabimin — dhe numërohet si përpjekje e plotë.
    """

    number: int
    generator: str
    text: str | None
    verification: VerificationResult | None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.verification is not None and self.verification.passed

    @property
    def violations(self) -> tuple[Violation, ...]:
        return self.verification.violations if self.verification else ()

    def failure(self) -> str:
        """Pse përpjekja nuk u dorëzua, në një rresht për regjistrin."""
        if self.error is not None:
            return f"gjeneruesi dështoi: {self.error}"
        kinds = sorted({v.type.value for v in self.violations})
        return f"{len(self.violations)} shkelje: {', '.join(kinds)}"


@dataclass(frozen=True, slots=True)
class Explanation:
    """Teksti i dorëzuar bashkë me rrugën që e prodhoi."""

    text: str
    delivery: Delivery
    attempts: tuple[Attempt, ...]
    verification: VerificationResult
    """Verifikimi i tekstit të dorëzuar — i përpjekjes që kaloi, ose i
    shabllonit."""


@dataclass(frozen=True, slots=True)
class Outcome:
    """Gjendja përfundimtare e një dokumenti dhe gjithçka që u prodhua."""

    document_id: UUID
    transitions: tuple[Transition, ...]
    channel: Channel | None = None
    context: GroundingContext | None = None
    explanation: Explanation | None = None

    @property
    def state(self) -> S:
        return self.transitions[-1].target

    @property
    def reason(self) -> str:
        return self.transitions[-1].reason


def process(
    document_id: UUID,
    path: Path,
    generator: Generator,
    *,
    ocr: Ocr | None = None,
    verifier: Verifier = verify,
) -> Outcome:
    """Drejton një dokument nga ngarkimi te një gjendje përfundimtare.

    Pa motor OCR, një dokument i skanuar përfundon në `FAILED_INGESTION`
    me arsyen e shkruar — jo në `NO_FINDINGS`. "Nuk u lexua" dhe "nuk
    kishte asgjë" janë dy përgjigje të ndryshme për pacientin.
    """
    log = StateLog()

    rejection = rejection_reason(path)
    if rejection is not None:
        log.advance(S.REJECTED, rejection)
        return Outcome(document_id, log.transitions)

    log.advance(S.INGESTING)
    routing = route(path)
    pages = routing.pages

    if routing.has_text:
        log.advance(S.TEXT_EXTRACTED, routing.reason)
    else:
        log.advance(S.OCR_RUNNING, routing.reason)
        if ocr is None:
            log.advance(S.FAILED_INGESTION, "motori OCR nuk është konfiguruar")
            return Outcome(document_id, log.transitions, routing.channel)
        try:
            pages = ocr(path)
        except Exception as error:
            log.advance(S.FAILED_INGESTION, f"OCR dështoi: {_describe(error)}")
            return Outcome(document_id, log.transitions, routing.channel)
        log.advance(S.TEXT_EXTRACTED, f"OCR: {len(pages)} faqe")

    log.advance(S.PARSING)
    grounding = build_grounding(document_id, pages)
    context = grounding.context

    if not grounding.has_content:
        log.advance(S.NO_FINDINGS, "asnjë vlerë laboratorike dhe asnjë pohim i mjekut")
        return Outcome(document_id, log.transitions, routing.channel, context)

    log.advance(
        S.GROUNDED, f"{len(context.findings)} gjetje, {len(context.assertions)} pohime"
    )
    explanation = explain(context, generator, verifier=verifier, log=log)
    return Outcome(document_id, log.transitions, routing.channel, context, explanation)


def explain(
    context: GroundingContext,
    generator: Generator,
    *,
    verifier: Verifier = verify,
    log: StateLog | None = None,
) -> Explanation:
    """Cikli gjenerim → verifikim, me rigjenerim dhe shabllon rezervë.

    Përpjekja e dytë i merr në kërkesë shkeljet e së parës. Pas një
    përpjekjeje që dështoi me përjashtim, e dyta nis pa shkelje: nuk ka
    tekst për të korrigjuar, vetëm një thirrje për të përsëritur.
    """
    log = log or StateLog(start=S.GROUNDED)
    attempts: list[Attempt] = []
    why = ""

    for number in range(1, MAX_GENERATION_ATTEMPTS + 1):
        log.advance(S.GENERATING, why, attempt=number)
        feedback = attempts[-1].violations if attempts else ()
        attempt = _attempt(number, context, generator, feedback, verifier, log)
        attempts.append(attempt)

        if attempt.passed:
            log.advance(S.DELIVERED, "verifikimi kaloi pa shkelje", attempt=number)
            return Explanation(
                attempt.text, Delivery.GENERATED, tuple(attempts), attempt.verification
            )
        why = attempt.failure()

    log.advance(S.TEMPLATE_FALLBACK, f"SP8 — {why}")
    text = templates.build(context)
    verification = verifier(context, text)
    log.advance(S.DELIVERED, "shablloni determinist")
    return Explanation(text, Delivery.TEMPLATE, tuple(attempts), verification)


def _attempt(
    number: int,
    context: GroundingContext,
    generator: Generator,
    feedback: tuple[Violation, ...],
    verifier: Verifier,
    log: StateLog,
) -> Attempt:
    try:
        text = generator(context, feedback)
    except Exception as error:
        return Attempt(number, generator.name, None, None, _describe(error))

    log.advance(S.VERIFYING, attempt=number)
    return Attempt(number, generator.name, text, verifier(context, text))


def _describe(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"
