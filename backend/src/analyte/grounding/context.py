"""
Bashkimi i të dyja degëve në GroundingContext.

Ky është vendi ku Dega A dhe Dega B takohen.

"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from analyte.domain.models import GroundingContext
from analyte.ingestion.pdf_text import PageText

from .branch_a import advice as branch_a_advice
from .branch_a import patterns
from .branch_a.extract import Extraction, extract
from .branch_b import assertions as branch_b_assertions
from .branch_b import terminology
from .branch_b.crossref import build_cross_references


@dataclass(frozen=True, slots=True)
class Grounding:
    """Konteksti bashkë me atë që u desh për ta ndërtuar.

    Teksti i narrativës dhe rreshtat e hedhur nuk hyjnë në kontekst — ato
    janë material auditimi dhe analize gabimesh, jo lëndë për modelin
    gjuhësor.
    """

    context: GroundingContext
    narrative_text: str
    extraction: Extraction

    @property
    def has_content(self) -> bool:
        return not self.context.is_empty()


def build(
    document_id: UUID, pages: tuple[PageText, ...], *, ocr_guard: bool = True, advice: bool = True
) -> Grounding:
    """Ndërton kontekstin nga faqet e lexuara të një dokumenti.

    `ocr_guard` ndez kontrollin e besueshmërisë për faqet e OCR-së (ADR 0020). Shërbimi e ka të ndezur; eksperimentet e
    ngrira (E7–E9, të matura para tij) e kalojnë të fikur, që cache-i i modelit dhe rezultatet e tyre të mbeten të vlefshme.

    `advice` lidh këshillat me burim të tabelës me gjetjet jashtë intervalit (ADR 0023). Po ashtu: i ndezur te shërbimi,
    i fikur te eksperimentet e ngrira, sepse këshilla hyn në kërkesën e modelit dhe në shabllon dhe do t'i ndryshonte
    kontekstet, çelësat e cache-it dhe rezultatet e matura para saj.
    """
    findings = extract(pages, ocr_guard=ocr_guard)
    narrative = branch_b_assertions.find_report_text(pages)

    assertions = branch_b_assertions.extract_assertions(narrative)
    context = GroundingContext(
        document_id=document_id,
        findings=findings.findings,
        assertions=assertions,
        cross_refs=build_cross_references(findings.findings, assertions),
        glossary=terminology.glossary_for(narrative),
        unexplained_terms=branch_b_assertions.unexplained_terms(narrative),
        patterns=patterns.detect(findings.findings),
        advice=branch_a_advice.attach(findings.findings) if advice else (),
    )
    return Grounding(context=context, narrative_text=narrative, extraction=findings)
