"""
Nga narrativa e mjekut te pohimet e strukturuara.

"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from analyte import textnorm
from analyte.domain.enums import AssertionKind, Direction
from analyte.domain.models import ReportAssertion
from analyte.grounding.branch_a import loinc
from analyte.ingestion.pdf_text import PageText
from analyte.textnorm import fold, words

from . import hedging, negation, terminology

REPORT_HEADINGS: tuple[str, ...] = (
    "vleresimi i mjekut",
    "koment klinik",
    "interpretimi",
    "mendimi i mjekut",
)
"""Titujt nën të cilët fillon teksti i lirë."""

REPORT_TERMINATORS: tuple[str, ...] = (
    "mjeku pergjegjes",
    "nenshkrimi",
    "firma",
)
"""Rreshtat që e mbyllin tekstin e lirë. Nënshkrimi nuk është narrativë."""

RECOMMENDATION_MARKERS: tuple[str, ...] = (
    "rekomandohet",
    "keshillohet",
    "sugjerohet kontroll",
    "duhet perseritur",
    "nevojitet",
    "nevoja per",
    "eshte e nevojshme",
    "kerkohet",
    "indikohet",
)
"""Shenjat e rekomandimit. Pesë të fundit shtuar për shqipen e vërtetë (grupi C): "nuk nevojitet kontroll", "nevoja për
rikontroll" — mohimi i një rekomandimi mbetet rekomandim me polaritet të mohuar."""

INCREASE_MARKERS: tuple[str, ...] = ("mbi intervalin", "e rritur", "te rritura", "i rritur")
DECREASE_MARKERS: tuple[str, ...] = ("nen intervalin", "e ulet", "te ulura", "i ulet")
NORMAL_MARKERS: tuple[str, ...] = ("brenda intervalit", "brenda kufijve", "normale")

INCREASE_EXTENDED: tuple[str, ...] = (
    "e larte",
    "i larte",
    "te larta",
    "te larte",
    "rritja e",
    "rritje e",
    "ngritja e",
    "ngritur",
    "tejkalon",
    "mbi kufirin",
    "mbi normen",
    "u rrit",
    "rritet",
)
DECREASE_EXTENDED: tuple[str, ...] = (
    "te ulta",
    "te ulet",
    "e ulur",
    "i ulur",
    "ulja e",
    "ulje e",
    "renia e",
    "u ul",
    "ulet",
    "nen kufirin",
    "nen normen",
    "i reduktuar",
    "e reduktuar",
    "te reduktuara",
    "te reduktuar",
)
NORMAL_EXTENDED: tuple[str, ...] = (
    "brenda normes",
    "ne rregull",
    "brenda parametrave",
    "brenda vlerave referente",
)
"""Fjalori i zgjeruar i drejtimit (`r1.4`, grupi C dhe auditi): mbiemrat e thjeshtë ("të larta"), emrat ("rritja e") dhe
foljet ("u rrit"). Kërkohen si fjalë të plota, jo si nënvargje: "ulet" nuk duhet të gjendet brenda një fjale tjetër."""

MAX_NAME_TOKENS = 3
"""Emri më i gjatë i analitit në tabelë ka tri fjalë."""


@dataclass(frozen=True, slots=True)
class Sentence:
    """Një fjali me pozicionin e saj në tekstin e plotë."""

    text: str
    start: int
    end: int


def find_report_text(pages: tuple[PageText, ...]) -> str:
    """Nxjerr tekstin e lirë të mjekut nga faqet e lexuara.

    Rreshtat e mbështjellë bashkohen me një hapësirë të vetme — pikërisht
    veprimi i kundërt i atij që i mbështolli. Kështu teksti i rindërtuar
    është varg për varg i njëjtë me atë që u shtyp, dhe pozicionet e
    pohimeve mbeten të krahasueshme me anotimin.
    """
    collected: list[str] = []
    capturing = False

    for page in pages:
        for row in page.rows:
            folded = fold(row.text)
            if not capturing:
                if any(folded.startswith(heading) for heading in REPORT_HEADINGS):
                    capturing = True
                continue
            if any(folded.startswith(end) for end in REPORT_TERMINATORS):
                return " ".join(collected).strip()
            collected.append(row.text.strip())

    return " ".join(collected).strip()


def split_sentences(text: str) -> tuple[Sentence, ...]:
    """Ndan tekstin në fjali, duke ruajtur pozicionet.

    Ndarja është e thjeshtë me qëllim. Narrativa e raporteve është prozë e
    shkurtër pa shkurtime me pikë; një ndarës më i zgjuar do të fshihte se
    ku e ka burimin secili pohim.
    """
    return tuple(Sentence(text_, start, end) for text_, start, end in textnorm.sentences(text))


def find_analyte(sentence: str) -> str | None:
    """Kodi LOINC i analitit të përmendur, nëse ka ndonjë.

    Kërkohen së pari emrat më të gjatë: "HDL-kolesteroli" nuk duhet të
    lexohet si "kolesteroli", sepse ato janë dy analite të ndryshme me dy
    intervale të ndryshme.
    """
    tokens = words(sentence)
    for size in range(MAX_NAME_TOKENS, 0, -1):
        for index in range(len(tokens) - size + 1):
            start = tokens[index][1]
            end = tokens[index + size - 1][2]
            code = loinc.resolve(sentence[start:end])
            if code is not None:
                return code
    return None


def _has_word(folded: str, markers: tuple[str, ...]) -> bool:
    padded = f" {folded} "
    return any(f" {marker} " in padded for marker in markers)


def find_direction(sentence: str, *, extended: bool = False) -> Direction:
    """Drejtimi i pohuar në fjali.

    Mohimi nuk e përmbys drejtimin këtu: "nuk rezulton mbi intervalin" ka
    drejtim INCREASED dhe polaritet NEGATED. Bashkimi i të dyjave në një
    fushë të vetme do ta bënte të pamundur dallimin mes "është i ulët" dhe
    "nuk është i lartë", të cilat nuk janë e njëjta gjë.
    """
    folded = fold(sentence)
    if any(marker in folded for marker in INCREASE_MARKERS):
        return Direction.INCREASED
    if any(marker in folded for marker in DECREASE_MARKERS):
        return Direction.DECREASED
    if any(marker in folded for marker in NORMAL_MARKERS):
        return Direction.NORMAL
    if extended:
        # Rendi i njëjtë (rritje, ulje, normal), por mbi fjalorin e zgjeruar dhe me fjalë të plota.
        if _has_word(folded, INCREASE_EXTENDED):
            return Direction.INCREASED
        if _has_word(folded, DECREASE_EXTENDED):
            return Direction.DECREASED
        if _has_word(folded, NORMAL_EXTENDED):
            return Direction.NORMAL
    return Direction.UNSPECIFIED


def _kind(sentence: str, code: str | None, has_term: bool) -> AssertionKind | None:
    folded = fold(sentence)
    if any(marker in folded for marker in RECOMMENDATION_MARKERS):
        return AssertionKind.RECOMMENDATION
    if code is not None:
        return AssertionKind.FINDING
    if has_term:
        return AssertionKind.TERM_MENTION
    return None


def _mentions_term(sentence: str, is_known: Callable[[str], bool]) -> bool:
    """A përmend fjalia ndonjë term mjekësor, të njohur apo jo?

    Termi i panjohur prodhon pohim njësoj si ai i njohuri. Kjo është ana e
    dytë e SP6 dhe jo hollësi: sistemi duhet ta vërejë fjalinë për ta
    shënuar termin si të pashpjeguar. Po ta linim pa pohim, fjalia do të
    zhdukej nga çdo shtresë e mëpasme dhe "nuk e shpjegojmë" do të bëhej
    "nuk e pamë fare" — dy gjëra që duken njësoj në dalje dhe janë krejt
    të ndryshme në auditim.
    """
    if terminology.detect_terms(sentence):
        return True
    return bool(terminology.detect_unknown_terms(sentence, is_known))


def extract_assertions(
    text: str, *, new_id: Callable[[], object] = uuid4
) -> tuple[ReportAssertion, ...]:
    """Pohimet e nxjerra nga narrativa."""
    assertions: list[ReportAssertion] = []
    is_known = _known_predicate()

    for sentence in split_sentences(text):
        span = sentence.text.rstrip(".!?").rstrip()
        if not span:
            continue

        code = find_analyte(sentence.text)
        has_term = _mentions_term(sentence.text, is_known)
        kind = _kind(sentence.text, code, has_term)
        if kind is None:
            continue

        assertions.append(
            ReportAssertion(
                id=new_id(),
                text_span=span,
                analyte_code=code if kind is AssertionKind.FINDING else None,
                direction=find_direction(sentence.text, extended=True),
                polarity=negation.polarity_of(sentence.text),
                certainty=hedging.certainty_of(sentence.text),
                kind=kind,
                char_start=sentence.start,
                char_end=sentence.start + len(span),
            )
        )

    return tuple(assertions)


def _known_predicate() -> Callable[[str], bool]:
    """Çfarë e njeh sistemi: tabela terminologjike dhe emrat e analiteve."""
    return terminology.any_of((terminology.known_term_predicate(), loinc.is_known))


def unexplained_terms(text: str) -> tuple[str, ...]:
    """Termat me trajtë mjekësore që nuk i njeh as tabela, as analitet (SP6)."""
    return terminology.detect_unknown_terms(text, _known_predicate())
