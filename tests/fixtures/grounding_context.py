"""
Konteksti referues i përdorur nga të gjitha testet.

Ky fixture i paraprin çdo komponenti tjetër të sistemit. Shtresa e
gjenerimit, shtresa e verifikimit dhe gjeneruesi i të dhënave
sintetike testohen kundrejt tij përpara se ata të ekzistojnë.

Përmbajtja imiton një analizë reale me kombinim gjetjesh që mbulon
rastet e rëndësishme:
  - një vlerë normale
  - një vlerë të lartë
  - një vlerë kritike (aktivizon SP4 dhe R4)
  - një vlerë pa interval referent (aktivizon SP5)
  - një pohim të mohuar (aktivizon R5)
  - një pohim me hedge (aktivizon R6)
  - një rekomandim (aktivizon R8)
  - një term të pashpjeguar (aktivizon SP6)
  - të katër gjendjet e krahasimit të kryqëzuar
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from analyte.domain.enums import (
    AnalyteStatus,
    AssertionKind,
    Certainty,
    CrossReferenceState,
    Direction,
    Polarity,
    ReferenceSource,
)
from analyte.domain.models import (
    AnalyteFinding,
    BoundingBox,
    CrossReference,
    GlossaryEntry,
    GroundingContext,
    ReportAssertion,
)

DOCUMENT_ID = UUID("11111111-1111-1111-1111-111111111111")
MEASURED = date(2026, 3, 14)


def build_reference_context() -> GroundingContext:
    glukoza = AnalyteFinding(
        id=UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        analyte_code="2345-7",
        analyte_name_raw="Glukoza (esëll)",
        analyte_name_canonical="Glukozë në serum",
        value_raw="128",
        value=Decimal(128),
        unit_raw="mg/dL",
        unit_canonical="mg/dL",
        value_canonical=Decimal(128),
        ref_low=Decimal(70),
        ref_high=Decimal(99),
        ref_source=ReferenceSource.DOCUMENT,
        status=AnalyteStatus.HIGH,
        severity=Decimal("1.0"),  # (128-99)/(99-70)
        page=1,
        bbox=BoundingBox(x0=72.0, y0=310.5, x1=520.0, y1=324.0),
        measured_at=MEASURED,
        flag_in_document="H",
    )

    hemoglobina = AnalyteFinding(
        id=UUID("aaaaaaaa-0000-0000-0000-000000000002"),
        analyte_code="718-7",
        analyte_name_raw="Hemoglobina",
        analyte_name_canonical="Hemoglobinë në gjak",
        value_raw="13,4",
        value=Decimal("13.4"),
        unit_raw="g/dL",
        unit_canonical="g/dL",
        value_canonical=Decimal("13.4"),
        ref_low=Decimal("12.0"),
        ref_high=Decimal("16.0"),
        ref_source=ReferenceSource.DOCUMENT,
        status=AnalyteStatus.NORMAL,
        severity=None,
        page=1,
        measured_at=MEASURED,
    )

    kaliumi = AnalyteFinding(
        id=UUID("aaaaaaaa-0000-0000-0000-000000000003"),
        analyte_code="2823-3",
        analyte_name_raw="Kaliumi",
        analyte_name_canonical="Kalium në serum",
        value_raw="6,9",
        value=Decimal("6.9"),
        unit_raw="mmol/L",
        unit_canonical="mmol/L",
        value_canonical=Decimal("6.9"),
        ref_low=Decimal("3.5"),
        ref_high=Decimal("5.1"),
        ref_source=ReferenceSource.DOCUMENT,
        status=AnalyteStatus.CRITICAL_HIGH,
        severity=Decimal("1.125"),  # (6.9-5.1)/(5.1-3.5)
        page=1,
        measured_at=MEASURED,
    )

    # Pa interval referent të shtypur dhe pa zë në tabelën e brendshme:
    # SP5 kërkon refuzim të interpretimit.
    ferritina = AnalyteFinding(
        id=UUID("aaaaaaaa-0000-0000-0000-000000000004"),
        analyte_code="2276-4",
        analyte_name_raw="Ferritina",
        analyte_name_canonical="Ferritinë në serum",
        value_raw="212",
        value=Decimal(212),
        unit_raw="ng/mL",
        unit_canonical="ng/mL",
        value_canonical=Decimal(212),
        ref_source=ReferenceSource.NONE,
        status=AnalyteStatus.UNINTERPRETABLE,
        page=2,
        measured_at=MEASURED,
    )

    # Pohimet nga narrativa e mjekut
    # Teksti burimor i imituar:
    #   "Glukoza e rritur është konfirmuar. Nuk ka shenja të anemisë.
    #    Rritja e transaminazave është e mundshme. Rekomandohet kontroll
    #    pas 3 muajsh. Vlerësohet gjendja e përgjithshme e eritropoezës."

    poh_glukoza = ReportAssertion(
        id=UUID("bbbbbbbb-0000-0000-0000-000000000001"),
        text_span="Glukoza e rritur është konfirmuar",
        analyte_code="2345-7",
        direction=Direction.INCREASED,
        polarity=Polarity.AFFIRMED,
        certainty=Certainty.CONFIRMED,
        kind=AssertionKind.FINDING,
        char_start=0,
        char_end=33,
    )

    poh_anemia = ReportAssertion(
        id=UUID("bbbbbbbb-0000-0000-0000-000000000002"),
        text_span="Nuk ka shenja të anemisë",
        analyte_code="718-7",
        direction=Direction.DECREASED,
        polarity=Polarity.NEGATED,
        certainty=Certainty.CONFIRMED,
        kind=AssertionKind.FINDING,
        char_start=35,
        char_end=59,
    )

    poh_alt = ReportAssertion(
        id=UUID("bbbbbbbb-0000-0000-0000-000000000003"),
        text_span="Rritja e transaminazave është e mundshme",
        analyte_code="1742-6",  # ALT — i përmendur por i pamatur
        direction=Direction.INCREASED,
        polarity=Polarity.AFFIRMED,
        certainty=Certainty.HEDGED,
        kind=AssertionKind.FINDING,
        char_start=61,
        char_end=100,
    )

    rekomandimi = ReportAssertion(
        id=UUID("bbbbbbbb-0000-0000-0000-000000000004"),
        text_span="Rekomandohet kontroll pas 3 muajsh",
        analyte_code=None,
        direction=Direction.UNSPECIFIED,
        polarity=Polarity.AFFIRMED,
        certainty=Certainty.CONFIRMED,
        kind=AssertionKind.RECOMMENDATION,
        char_start=102,
        char_end=135,
    )

    # Krahasimi i kryqëzuar: të katër gjendjet
    refs = (
        CrossReference(
            analyte_code="2345-7",
            state=CrossReferenceState.AGREEMENT,
            assertion_id=poh_glukoza.id,
            finding_id=glukoza.id,
        ),
        CrossReference(
            analyte_code="718-7",
            state=CrossReferenceState.AGREEMENT,
            assertion_id=poh_anemia.id,
            finding_id=hemoglobina.id,
        ),
        CrossReference(
            analyte_code="1742-6",
            state=CrossReferenceState.MENTIONED_NOT_MEASURED,
            assertion_id=poh_alt.id,
        ),
        CrossReference(
            analyte_code="2823-3",
            state=CrossReferenceState.MEASURED_NOT_MENTIONED,
            finding_id=kaliumi.id,
        ),
    )

    glossary = (
        GlossaryEntry(
            term="transaminaza",
            explanation_sq="enzima që lidhen me funksionin e mëlçisë",
            source_ref="[BURIMI — plotësohet gjatë ndërtimit të tabelës]",
            category="enzima",
            synonyms=("ALT", "AST"),
        ),
        GlossaryEntry(
            term="anemi",
            explanation_sq="nivel i ulët i hemoglobinës në gjak",
            source_ref="[BURIMI — plotësohet gjatë ndërtimit të tabelës]",
            category="gjendje",
        ),
    )

    return GroundingContext(
        document_id=DOCUMENT_ID,
        findings=(glukoza, hemoglobina, kaliumi, ferritina),
        assertions=(poh_glukoza, poh_anemia, poh_alt, rekomandimi),
        cross_refs=refs,
        glossary=glossary,
        # "eritropoeza" shfaqet në raport por mungon në tabelë → SP6
        unexplained_terms=("eritropoeza",),
    )
