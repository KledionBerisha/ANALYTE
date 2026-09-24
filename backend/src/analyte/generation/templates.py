"""
Shpjegimi determinist me shabllon.

Ky është teksti që shfaqet kur verifikimi dështon dy herë (SP8), dhe
njëkohësisht kushti bazë i ablacionit: dalje plotësisht e bazuar, e
prodhuar pa model gjuhësor.

Ai ka edhe një rol të tretë, që nuk ishte i planifikuar dhe doli i
dobishëm: teksti i tij është i garantuar i saktë, prandaj shërben si
material i pastër mbi të cilin ndërtohet korpusi i korruptuar. Një
shpjegim i prishur me qëllim nga një bazë e pastër ka etiketë të sigurt,
ndërsa një i prishur nga dalja e një modeli gjuhësor do të kishte etiketë
të sigurt vetëm nëse dalja fillestare ishte e saktë — gjë që duhet matur
dhe jo supozuar.

**Asnjë numër që nuk është në kontekst.** Shablloni shtyp vetëm vlerën
dhe kufijtë e intervalit, pra pikërisht bashkësinë që rregulli R1 lejon.
**Asnjë folje me gjini.** Ndërtimi "Për {emri} vlera e matur është ..."
funksionon me çdo emër analiti, në njëjës apo shumës, pa përshtatje.
"""

from __future__ import annotations

from decimal import Decimal

from analyte.domain.enums import AnalyteStatus
from analyte.domain.models import AnalyteFinding, GroundingContext
from analyte.domain.policy import (
    ATTRIBUTION_PREFIX_SQ,
    CRITICAL_BANNER_SQ,
    DISCLAIMER_SQ,
    UNEXPLAINED_TERM_NOTICE_SQ,
    UNINTERPRETABLE_NOTICE_SQ,
)

POSITION: dict[AnalyteStatus, str] = {
    AnalyteStatus.CRITICAL_LOW: "dukshëm nën intervalin referent",
    AnalyteStatus.LOW: "nën intervalin referent",
    AnalyteStatus.NORMAL: "brenda intervalit referent",
    AnalyteStatus.HIGH: "mbi intervalin referent",
    AnalyteStatus.CRITICAL_HIGH: "dukshëm mbi intervalin referent",
}


def build(context: GroundingContext) -> str:
    """Ndërton shpjegimin me shabllon për një kontekst të dhënë.

    Rendi është i detyruar nga politika: njoftimi për vlerat kritike vjen
    përpara çdo teksti shpjegues (SP4), dhe shënimi për profesionistin
    shëndetësor mbyll çdo dalje (SP7).
    """
    parts: list[str] = []

    if context.critical_findings():
        parts.append(CRITICAL_BANNER_SQ)

    for finding in context.findings:
        parts.append(_finding_sentence(finding))

    parts.extend(_term_sentences(context))
    parts.extend(_quoted_assertions(context))
    parts.append(DISCLAIMER_SQ)

    return " ".join(part for part in parts if part)


def _finding_sentence(finding: AnalyteFinding) -> str:
    name = finding.analyte_name_canonical
    value = _number(finding.value_canonical)
    unit = finding.unit_canonical

    if finding.status is AnalyteStatus.UNINTERPRETABLE:
        # SP5: njoftimi zëvendëson interpretimin, nuk e shoqëron atë.
        return f"Për {name} vlera e matur është {value} {unit}. {UNINTERPRETABLE_NOTICE_SQ}"

    position = POSITION[finding.status]
    interval = _interval(finding)
    return f"Për {name} vlera e matur është {value} {unit}, {position}{interval}."


def _interval(finding: AnalyteFinding) -> str:
    """Kufijtë, aty ku ekzistojnë.

    Pacienti duhet të mund ta shohë intervalin krahas vlerës; prandaj
    rregulli R1 i lejon shprehimisht të dy kufijtë ndër numrat e
    mbështetur.
    """
    low, high = finding.ref_low, finding.ref_high
    if low is not None and high is not None:
        return f" ({_number(low)} - {_number(high)})"
    if high is not None:
        return f" (deri {_number(high)})"
    if low is not None:
        return f" (nga {_number(low)})"
    return ""


def _term_sentences(context: GroundingContext) -> list[str]:
    """Shpjegimet e termave, dhe refuzimi për ata që mungojnë (SP6)."""
    out = [f"{entry.term.capitalize()} do të thotë {entry.explanation_sq}." for entry in context.glossary]
    for term in context.unexplained_terms:
        out.append(f"Raporti përmend termin “{term}”. {UNEXPLAINED_TERM_NOTICE_SQ}")
    return out


def _quoted_assertions(context: GroundingContext) -> list[str]:
    """Pohimet e mjekut, të ruajtura fjalë për fjalë dhe të atribuuara.

    Riprodhimi fjalë për fjalë e zgjidh njëherësh atë që rregullat R5, R6
    dhe R8 kërkojnë: polariteti, rezerva dhe rekomandimi mbijetojnë sepse
    teksti nuk preket fare. Një rekomandim i riformuluar është rekomandim
    i ndryshuar, dhe shablloni nuk ka si ta dijë nëse ndryshimi ishte i
    padëmshëm.

    Atribuimi nuk është mirësjellje. Ai e ndan atë që thotë sistemi nga
    ajo që citon ai, dhe vetëm kështu verifikimi mund t'i masë të dyja me
    masën e duhur: pohimet e veta kundrejt matjeve, citimet kundrejt
    burimit.
    """
    return [
        f"{ATTRIBUTION_PREFIX_SQ} {assertion.text_span}."
        for assertion in context.assertions
    ]


def _number(value: Decimal) -> str:
    """Numri pa zero të panevojshme në fund.

    `Decimal("13.40")` dhe `Decimal("13.4")` janë i njëjti numër, por
    vargjet e tyre ndryshojnë dhe teksti do të dukej i papastër.
    """
    normalized = value.normalize()
    if normalized == normalized.to_integral_value():
        normalized = normalized.quantize(Decimal(1))
    return f"{normalized:f}"
