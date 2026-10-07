"""
Bazat e përbashkëta të shtresës së verifikimit.

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from analyte import textnorm
from analyte.domain.enums import DetectedBy, ViolationType
from analyte.domain.models import GroundingContext, Violation
from analyte.domain.policy import ATTRIBUTION_PREFIX_SQ
from analyte.grounding.branch_a import loinc
from analyte.textnorm import words

from . import ruleset


def is_attributed(sentence: str) -> bool:
    """A është kjo fjali citim i shënuar i mjekut?"""
    return sentence.lstrip().startswith(ATTRIBUTION_PREFIX_SQ)


NUMBER_TOKEN = re.compile(r"(?<![^\W_])\d+(?:[.,]\d+)?(?![^\W_])")
MAX_NAME_TOKENS = 3
MAX_NAME_TOKENS_MODERN = 4
"""`r1.4`: "Vitamina D 25-OH" ka katër fjalë kur shkruhet me trajtë të shquar."""


@dataclass(frozen=True, slots=True)
class Sentence:
    """Një fjali e daljes së gjeneruar."""

    text: str
    index: int


def sentences(text: str) -> tuple[Sentence, ...]:
    return tuple(
        Sentence(text_, position) for position, (text_, _, _) in enumerate(textnorm.sentences(text))
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
    masked = mask_known_strings(text, context)
    if ruleset.modern():
        # r1.4: emrat e analiteve maskohen edhe në trajtën e shquar ("Vitamina D 25-OH"), jo vetëm në trajtën e tabelës.
        for _, start, end in mentions(text, context):
            masked = masked[:start] + " " * (end - start) + masked[end:]
    for match in NUMBER_TOKEN.finditer(masked):
        raw = match.group()
        try:
            found.append((Decimal(raw.replace(",", ".")), raw))
        except InvalidOperation:  # pragma: no cover - i pamundur me këtë regex
            continue
    return found


def without_glosses(text: str, context: GroundingContext) -> str:
    """Zëvendëson me hapësira shpjegimet e fjalorit që shfaqen fjalë për fjalë në tekst (`r1.4`).

    Shpjegimi i hemoglobinës ("proteina që bart oksigjenin në qelizat e kuqe") përmban "qelizat e kuqe", që është emër i
    eritrociteve; një fjali që thjesht e jep shpjegimin nuk flet për eritrocitet. R2 e pranon këtë përmes bashkësisë së
    analiteve të njohura; rregullat e drejtimit dhe të lidhjes së numrave kanë nevojë ta heqin para se të njohin analitet.
    """
    for entry in context.glossary:
        explanation = entry.explanation_sq.strip().rstrip(".")
        if len(explanation) >= 8:
            text = re.sub(
                re.escape(explanation), lambda m: " " * len(m.group()), text, flags=re.IGNORECASE
            )
    return text


def mentions(text: str, context: GroundingContext) -> list[tuple[str, int, int]]:
    """Analitet e përmendura me pozicionet e tyre: (kodi LOINC, fillimi, fundi), pa mbivendosje.

    Kërkohen emrat më të gjatë të parët, që "Kolesterol HDL" të mos
    lexohet si "Kolesterol" — dy analite me dy intervale.

    Njësitë maskohen të parat: "mg" brenda `mg/dL` është varianti i
    shtypur i magnezit, dhe pa maskim çdo vlerë në miligramë do të
    raportonte një analit të papërmendur.

    `r1.4`: pranohet edhe trajta e shquar ("Kolesteroli HDL") dhe emri deri në katër fjalë.
    """
    text = mask_units(text, context)
    tokens = words(text)
    modern = ruleset.modern()
    resolve = loinc.resolve_inflected if modern else loinc.resolve
    longest = MAX_NAME_TOKENS_MODERN if modern else MAX_NAME_TOKENS
    found: list[tuple[str, int, int]] = []
    taken: set[int] = set()

    for size in range(longest, 0, -1):
        for index in range(len(tokens) - size + 1):
            if any(position in taken for position in range(index, index + size)):
                continue
            start, end = tokens[index][1], tokens[index + size - 1][2]
            code = resolve(text[start:end])
            if code is not None:
                taken.update(range(index, index + size))
                found.append((code, start, end))
    return found


def analytes_in(text: str, context: GroundingContext) -> list[str]:
    """Kodet LOINC të analiteve të përmendura, pa përsëritje.

    Rendi është ai i zbulimit (emrat më të gjatë të parët), si në r1.3: lista e shkeljeve futet te kërkesa e rigjenerimit, dhe
    një rend tjetër do të ndryshonte çelësat e cache-it të modelit."""
    codes: list[str] = []
    for code, _, _ in mentions(text, context):
        if code not in codes:
            codes.append(code)
    return codes


def violation(
    kind: ViolationType, sentence: str, evidence: str, detected_by: DetectedBy = DetectedBy.RULE
) -> Violation:
    """Shkelje e zbuluar nga një rregull.

    Rregullat nuk mbajnë besueshmëri: ato ose e shohin shkeljen ose jo.
    Modeli i domenit e zbaton këtë, prandaj kalimi i një vlere këtu do të
    dështonte në ndërtim.
    """
    return Violation(type=kind, detected_by=detected_by, sentence=sentence, evidence=evidence)
