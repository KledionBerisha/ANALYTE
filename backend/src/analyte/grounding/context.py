"""
Bashkimi i të dyja degëve në GroundingContext.

Ky është vendi ku Dega A dhe Dega B takohen, dhe i vetmi objekt që kalon
më tej. Pas këtij funksioni, asnjë shtresë nuk ka qasje te dokumenti i
papërpunuar as te teksti i nxjerrë prej tij — garancia arkitekturore e
punimit e shprehur si rrjedhë të dhënash dhe jo si premtim.

Konteksti ndërtohet i plotë ose nuk ndërtohet fare. Modelet e domenit e
kontrollojnë vetë qëndrueshmërinë e brendshme: një krahasim i kryqëzuar
që i referohet një gjetjeje joekzistuese e ndal ndërtimin këtu, ku shkaku
është ende i dukshëm, në vend që të dështojë pa shpjegim te verifikimi.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from analyte.domain.models import GroundingContext
from analyte.ingestion.pdf_text import PageText

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


def build(document_id: UUID, pages: tuple[PageText, ...]) -> Grounding:
    """Ndërton kontekstin nga faqet e lexuara të një dokumenti."""
    findings = extract(pages)
    narrative = branch_b_assertions.find_report_text(pages)

    assertions = branch_b_assertions.extract_assertions(narrative)
    context = GroundingContext(
        document_id=document_id,
        findings=findings.findings,
        assertions=assertions,
        cross_refs=build_cross_references(findings.findings, assertions),
        glossary=terminology.glossary_for(narrative),
        unexplained_terms=branch_b_assertions.unexplained_terms(narrative),
    )
    return Grounding(context=context, narrative_text=narrative, extraction=findings)
