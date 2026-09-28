"""
Bazat e përbashkëta të shtresës së verifikimit.

Rregullat ndajnë tri veprime: ndarjen e daljes në fjali, nxjerrjen e
numrave prej saj, dhe njohjen e analiteve të përmendura. Secili prej tyre
ka një kurth që e bën më pak të drejtpërdrejtë seç duket.

**Emrat dhe njësitë nuk janë të dhëna.** Njësia `10^9/L` përmban "10" dhe
"9"; emri "Vitaminë D 25-OH" përmban "25"; shkronjat "mg" brenda `mg/dL`
janë varianti i shtypur i magnezit. Të lexuara si vlera dhe si analite të
përmendura, ato do të prodhonin shkelje në pothuajse çdo fjali.

Prandaj çdo varg i njohur maskohet përpara se teksti të shqyrtohet:
njësitë dhe emrat e analiteve para nxjerrjes së numrave, dhe njësitë para
njohjes së analiteve. Maskimi ruan gjatësinë, që pozicionet të mbeten të
përdorshme.

**Rregullat kanë qasje te konteksti i plotë.** Ky është dallim thelbësor
nga klasifikuesi i Fazës 7, i cili sheh vetëm fjalinë. Kur PK6 i krahason
të dy, krahasimi nuk është ndërmjet dy metodave mbi të njëjtin
informacion; kjo duhet thënë kur raportohen rezultatet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from analyte.domain.enums import DetectedBy, ViolationType
from analyte.domain.models import GroundingContext, Violation
from analyte.domain.policy import ATTRIBUTION_PREFIX_SQ
from analyte.grounding.branch_a import loinc
from analyte import textnorm
from analyte.textnorm import words

def is_attributed(sentence: str) -> bool:
    """A është kjo fjali citim i shënuar i mjekut?"""
    return sentence.lstrip().startswith(ATTRIBUTION_PREFIX_SQ)


NUMBER_TOKEN = re.compile(r"(?<![^\W_])\d+(?:[.,]\d+)?(?![^\W_])")
MAX_NAME_TOKENS = 3


@dataclass(frozen=True, slots=True)
class Sentence:
    """Një fjali e daljes së gjeneruar."""

    text: str
    index: int


def sentences(text: str) -> tuple[Sentence, ...]:
    return tuple(
        Sentence(text_, position)
        for position, (text_, _, _) in enumerate(textnorm.sentences(text))
    )


def _mask(text: str, strings: set[str]) -> str:
    """Zëvendëson vargjet e dhëna me hapësira të së njëjtës gjatësi.

    Zëvendësimi bëhet nga vargu më i gjatë te më i shkurtri, që `10^12/L`
    të mos maskohet pjesërisht si `10^1` dhe të lërë mbetje.

    Maskohen vetëm vargjet që mund të jenë emër ose njësi. OCR-ja prodhon
    "njësi" si "." ose "52,0": maskimi i pikës do t'i ndante të gjithë numrat
    dhjetorë të tekstit ("15.6" → "15 6"), dhe maskimi i "52,0" do ta fshihte
    pikërisht një numër nga R1 — rregulli do të heshte para një vlere të
    shpikur.
    """
    for value in sorted((s for s in strings if _maskable(s)), key=len, reverse=True):
        text = text.replace(value, " " * len(value))
    return text


def _maskable(value: str) -> bool:
    """Ka shkronjë, ose është simbol pa shifra dhe pa ndarës dhjetor ("%")."""
    if not value.strip():
        return False
    if any(c.isalpha() for c in value):
        return True
    return not any(c.isdigit() or c in ".," for c in value)


def mask_units(text: str, context: GroundingContext) -> str:
    """Fsheh njësitë e kontekstit."""
    units = {finding.unit_canonical for finding in context.findings}
    units |= {finding.unit_raw for finding in context.findings if finding.unit_raw}
    return _mask(text, units)


def mask_known_strings(text: str, context: GroundingContext) -> str:
    """Fsheh njësitë dhe emrat e analiteve.

    Emri i analitit mund të përmbajë shifra që janë pjesë e tij — "B12",
    "FT4", "25-OH" — dhe kufijtë e fjalës nuk mjaftojnë aty ku shifra
    ndahet me vizë.
    """
    names = {finding.analyte_name_canonical for finding in context.findings}
    names |= {finding.analyte_name_raw for finding in context.findings}
    return _mask(mask_units(text, context), names)


def numbers_in(text: str, context: GroundingContext) -> list[tuple[Decimal, str]]:
    """Numrat e përmendur në tekst, pa ata që janë pjesë e njësive."""
    found: list[tuple[Decimal, str]] = []
    for match in NUMBER_TOKEN.finditer(mask_known_strings(text, context)):
        raw = match.group()
        try:
            found.append((Decimal(raw.replace(",", ".")), raw))
        except InvalidOperation:  # pragma: no cover - i pamundur me këtë regex
            continue
    return found


def analytes_in(text: str, context: GroundingContext) -> list[str]:
    """Kodet LOINC të analiteve të përmendura, pa përsëritje.

    Kërkohen emrat më të gjatë të parët, që "Kolesterol HDL" të mos
    lexohet si "Kolesterol" — dy analite me dy intervale.

    Njësitë maskohen të parat: "mg" brenda `mg/dL` është varianti i
    shtypur i magnezit, dhe pa maskim çdo vlerë në miligramë do të
    raportonte një analit të papërmendur.
    """
    text = mask_units(text, context)
    tokens = words(text)
    found: list[str] = []
    taken: set[int] = set()

    for size in range(MAX_NAME_TOKENS, 0, -1):
        for index in range(len(tokens) - size + 1):
            if any(position in taken for position in range(index, index + size)):
                continue
            start, end = tokens[index][1], tokens[index + size - 1][2]
            code = loinc.resolve(text[start:end])
            if code is not None:
                taken.update(range(index, index + size))
                if code not in found:
                    found.append(code)
    return found


def violation(
    kind: ViolationType, sentence: str, evidence: str, detected_by: DetectedBy = DetectedBy.RULE
) -> Violation:
    """Shkelje e zbuluar nga një rregull.

    Rregullat nuk mbajnë besueshmëri: ato ose e shohin shkeljen ose jo.
    Modeli i domenit e zbaton këtë, prandaj kalimi i një vlere këtu do të
    dështonte në ndërtim.
    """
    return Violation(type=kind, detected_by=detected_by, sentence=sentence, evidence=evidence)
