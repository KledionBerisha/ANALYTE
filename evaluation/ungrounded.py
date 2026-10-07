"""
Kushti A i ablacionit (E6): modeli pa bazim.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analyte.domain.enums import ProcessingState
from analyte.domain.models import GroundingContext
from analyte.domain.policy import LEGACY_RULES_VERSION
from analyte.ingestion.pdf_text import PageText

from .pipeline import DocumentInput, PipelineOutput, _read_pages

UNGROUNDED_PROMPT_VERSION = "u1"

SYSTEM = (
    "Ti je një asistent që u shpjegon pacientëve rezultatet e analizave dhe "
    "raportet mjekësore në gjuhë të thjeshtë shqipe."
)


def build_prompt(pages: tuple[PageText, ...]) -> tuple[str, str]:
    text = "\n".join(row.text for page in pages for row in page.rows)
    user = (
        "Ky është dokumenti mjekësor i pacientit:\n\n"
        f"{text}\n\n"
        "Shpjegoja pacientit çfarë thotë ky dokument, në gjuhë të thjeshtë."
    )
    return SYSTEM, user


@dataclass(frozen=True, slots=True)
class UngroundedPipeline:
    """E6: dokumenti, pastaj modeli, pastaj numërimi i shkeljeve."""

    client: Any
    ocr: Any = None
    ablation: str = "E6"
    version: str = "1"
    ocr_guard: bool = False
    advice: bool = False
    """Këshillat me burim (ADR 0023); i fikur te eksperimentet e ngrira."""
    rules: str = LEGACY_RULES_VERSION
    """E6 mat shkeljet e tekstit pa bazim me katalogun e zgjedhur; parazgjedhja është r1.3 e ngrirë."""

    @property
    def name(self) -> str:
        suffix = "+ocr" if self.ocr is not None else ""
        return f"e6[{self.client.provider}:{self.client.model}:{UNGROUNDED_PROMPT_VERSION}]{suffix}"

    @property
    def generator(self) -> Any:
        """Klienti, që harness-i të regjistrojë modelin dhe kostot."""
        return self

    def run(self, document: DocumentInput) -> PipelineOutput:
        from analyte.generation.llm import ProviderError
        from analyte.grounding.context import build
        from analyte.orchestration.process import Attempt
        from analyte.verification.pipeline import verify

        pages, failure = _read_pages(document, self.ocr)
        if failure is not None:
            return PipelineOutput(
                context=GroundingContext(document_id=document.document_id),
                state=ProcessingState.FAILED_INGESTION,
                failures=(failure,),
            )

        grounding = build(document.document_id, pages, ocr_guard=self.ocr_guard, advice=self.advice)
        context = grounding.context
        if not grounding.has_content:
            return PipelineOutput(context=context, state=ProcessingState.NO_FINDINGS)

        system, user = build_prompt(pages)
        try:
            text = self.client.complete(system, user).text
        except ProviderError as error:
            # `ProviderUnavailable` e ndal ekzekutimin më lart (harness-i e kthen në
            # `RunAborted`); këtu mbetet vetëm një përgjigje e refuzuar ose e cunguar.
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
            attempts=(Attempt(1, self.name, text, verification),),
            delivered_verification=verification,
        )
