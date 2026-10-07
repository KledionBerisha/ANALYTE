"""
Porta e çidentifikimit: çfarë teksti të dokumentit lejohet t'i dërgohet ofruesit të modelit (ADR 0019).

"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from analyte import catalog
from analyte.domain.models import GroundingContext
from analyte.domain.policy import (
    ATTRIBUTION_PREFIX_SQ,
    CRITICAL_BANNER_SQ,
    DISCLAIMER_SQ,
    UNEXPLAINED_TERM_NOTICE_SQ,
    UNINTERPRETABLE_NOTICE_SQ,
)
from analyte.textnorm import fold_token, words


class Kind(str, Enum):
    """Lloji i asaj që u gjet. Vlerat ruhen te log-u i auditimit dhe te `documents.model_gate_kinds`."""

    NAME_LIKE = "name_like"
    TITLE = "title"
    DATE = "date"
    BIRTH_OR_AGE = "birth_or_age"
    PHONE = "phone"
    EMAIL = "email"
    URL = "url"
    LONG_NUMBER = "long_number"
    ID_TOKEN = "id_token"
    ADDRESS_CUE = "address_cue"
    CONTACT_CUE = "contact_cue"
    UNCATALOGUED = "uncatalogued"


# Fjalori i njohur

COMMON_WORDS: tuple[str, ...] = (
    # fjalë funksionale
    "i",
    "e",
    "të",
    "së",
    "në",
    "me",
    "pa",
    "për",
    "nga",
    "deri",
    "pas",
    "para",
    "mbi",
    "nën",
    "brenda",
    "jashtë",
    "dhe",
    "ose",
    "por",
    "që",
    "si",
    "nuk",
    "mos",
    "ende",
    "edhe",
    "vetëm",
    "shumë",
    "pak",
    "ka",
    "kanë",
    "është",
    "janë",
    "ishte",
    "ky",
    "kjo",
    "këtë",
    "këto",
    "ato",
    "ata",
    "ai",
    "ajo",
    "një",
    "disa",
    "çdo",
    "asnjë",
    "tjetër",
    "tjera",
    "kur",
    "ku",
    "pse",
    "nëse",
    "sepse",
    "megjithatë",
    "gjithashtu",
    "prandaj",
    "ndaj",
    "përveç",
    "midis",
    "mes",
    "gjatë",
    "rreth",
    "afër",
    "larg",
    "më",
    "po",
    "jo",
    "ose",
    "dhe",
    "apo",
    "ndërsa",
    "kurse",
    "pra",
    "ndonjë",
    "gjithë",
    "tërë",
    "secili",
    "secila",
    "vetë",
    "tashmë",
    "sërish",
    "përsëri",
    "tani",
    "më parë",
    "pastaj",
    "fillimisht",
    # folje dhe formulime të shënimeve klinike
    "mund",
    "duhet",
    "lejohet",
    "bëhet",
    "vlen",
    "mbetet",
    "vërehet",
    "vërehen",
    "shihet",
    "shihen",
    "tregon",
    "tregojnë",
    "sugjeron",
    "sugjerojnë",
    "mungon",
    "mungojnë",
    "përjashtohet",
    "rekomandohet",
    "këshillohet",
    "sugjerohet",
    "vlerësohet",
    "vlerësim",
    "vlerësimi",
    "përsëritet",
    "përsëritja",
    "përsëritje",
    "konsultohuni",
    "konsultë",
    "konsultim",
    "paraqitet",
    "paraqet",
    "rezulton",
    "rezultojnë",
    "ndjekje",
    "ndiqet",
    "ndiqen",
    "kontrollohet",
    "kontrollo",
    "kontrolli",
    "kontroll",
    "shqyrtohet",
    "interpretohet",
    "lidhet",
    "ndërlidhet",
    "tregohet",
    "konfirmohet",
    "dyshohet",
    "pritet",
    "mbahet",
    "ndryshon",
    "ndryshojnë",
    "ulet",
    "rritet",
    "qëndron",
    "qëndrojnë",
    "ruhet",
    "vazhdon",
    "vazhdojnë",
    # emra të shënimeve klinike
    "vlerat",
    "vlera",
    "vlerës",
    "rezultatet",
    "rezultati",
    "rezultatit",
    "analizat",
    "analiza",
    "analizave",
    "raporti",
    "raportit",
    "gjendja",
    "gjendje",
    "gjendjen",
    "funksioni",
    "funksionin",
    "shenja",
    "shenjat",
    "shenjave",
    "nivelet",
    "niveli",
    "nivelin",
    "numri",
    "numrin",
    "përqendrimi",
    "matja",
    "matjet",
    "prania",
    "mungesa",
    "rritje",
    "ulje",
    "shkallë",
    "shkalla",
    "intervali",
    "intervalin",
    "kufiri",
    "kufijtë",
    "normale",
    "normal",
    "lehtë",
    "lehta",
    "lehtë",
    "mesatare",
    "rëndë",
    "kritike",
    "kritik",
    "klinik",
    "klinike",
    "klinikë",
    "mjeku",
    "mjekun",
    "mjekut",
    "specialist",
    "specialisti",
    "specialistin",
    "pacienti",
    "pacientja",
    "pacientit",
    "pacientes",
    "pacient",
    "laboratori",
    "laboratorike",
    "laboratorit",
    "kontrolli",
    "gjaku",
    "gjakut",
    "urina",
    "urinës",
    "muaj",
    "muajsh",
    "muaji",
    "javë",
    "javësh",
    "ditë",
    "ditësh",
    "vit",
    "vjet",
    "viti",
    "tre",
    "dy",
    "një",
    "katër",
    "pesë",
    "gjashtë",
    "dhjetë",
    "shënim",
    "shënimi",
    "shënime",
    "diagnoza",
    "trajtim",
    "trajtimi",
    "terapi",
    "terapia",
    "ilaç",
    "ilaçe",
    "dieta",
    "dietë",
    "mënyra",
    "jetesës",
    "jetesa",
    "ushqim",
    "ushqimi",
    "kujdes",
    "kujdesi",
    "rutinë",
    "rutina",
    "mëtejshme",
    "mëtejshëm",
    "mëtejshëm",
    "tjetër",
    "tjetra",
    "tjetri",
    "vlerave",
    "vlerës",
)
"""Lista e mbyllur e fjalëve të zakonshme të shënimeve klinike që mund të hapin një fjali (dhe kështu të shkruhen me
shkronjë të madhe). Është e shkurtër me qëllim: çdo fjalë që mungon këtu e që shkruhet me shkronjë të madhe shënohet
`name_like`, dhe kjo është e dëshiruar (dështim i mbyllur). Fjalët që mund të jenë edhe emra vetjakë (p.sh.
"Besa", "Burim") nuk janë këtu, dhe një test e provon këtë me një listë emrash shembull."""

TITLES: frozenset[str] = frozenset(
    {
        "dr",
        "prof",
        "doc",
        "znj",
        "zj",
        "zonja",
        "zoti",
        "mr",
        "mrs",
        "ms",
        "msc",
        "phd",
        "ing",
        "av",
        "mag",
    }
)
"""Titujt që paraprijnë një emër. Shënohen vetë, edhe pa emër pas tyre."""

_ADDRESS_STEMS: tuple[str, ...] = (
    "rruga",
    "rruge",
    "lagj",
    "bulevard",
    "qytet",
    "fshat",
    "pallat",
    "apartament",
    "banon",
    "banim",
    "vendbanim",
    "adres",
    "vendlindj",
    "postar",
)
_ADDRESS_EXACT: frozenset[str] = frozenset({"rr", "bul", "blv"})
_CONTACT_STEMS: tuple[str, ...] = (
    "telefon",
    "celular",
    "mobil",
    "whatsapp",
    "viber",
    "email",
    "mail",
)
_CONTACT_EXACT: frozenset[str] = frozenset({"tel", "cel", "fax"})
_BIRTH_STEMS: tuple[str, ...] = ("lindur", "lindj", "datelind", "ditelind", "vjec", "mosh")
_MONTHS: tuple[str, ...] = (
    "janar",
    "shkurt",
    "mars",
    "prill",
    "maj",
    "qershor",
    "korrik",
    "gusht",
    "shtator",
    "tetor",
    "nentor",
    "dhjetor",
)

_POLICY_TEXTS = (
    CRITICAL_BANNER_SQ,
    DISCLAIMER_SQ,
    UNEXPLAINED_TERM_NOTICE_SQ,
    UNINTERPRETABLE_NOTICE_SQ,
    ATTRIBUTION_PREFIX_SQ,
)


def _tokens(text: str) -> Iterable[str]:
    return (fold_token(token) for token, _, _ in words(text))


@lru_cache(maxsize=1)
def vocabulary() -> frozenset[str]:
    """Fjalët (të normalizuara) që një fjalë me shkronjë të madhe lejohet të jetë.

    Burimet janë katalogu dhe teksti i politikës, jo një fjalor i përgjithshëm: emrat e analiteve, termat dhe
    sinonimet, fjalët e shpjegimeve, dhe `COMMON_WORDS`.
    """
    out: set[str] = set()
    for analyte in catalog.analytes_by_code().values():
        units = (analyte.unit, analyte.alt_unit or "")
        for form in (analyte.name_canonical_sq, analyte.narrative_name, *analyte.variants, *units):
            out.update(_tokens(form))
    for term in catalog.load_terminology():
        for form in (*term.surface_forms(), term.explanation_sq):
            out.update(_tokens(form))
    for text in _POLICY_TEXTS:
        out.update(_tokens(text))
    out.update(fold_token(word) for word in COMMON_WORDS)
    out.discard("")
    return frozenset(out)


@lru_cache(maxsize=1)
def _stems() -> frozenset[str]:
    """Rrënjët e fjalorit: çdo fjalë me të paktën gjashtë shkronja, e shkurtuar me një ose dy shkronja të fundit (jo nën
    pesë). Shqipja e ndryshon mbaresën (rritje, rritja, rritjes), dhe krahasimi mbi rrënjë i njeh lakimet pa fjalor të plotë."""
    return frozenset(
        word[:keep]
        for word in vocabulary()
        if len(word) >= 6
        for keep in (len(word), len(word) - 1, len(word) - 2)
        if keep >= 5
    )


def is_known_word(token: str) -> bool:
    """A është fjala te fjalori, ose një lakim i saj (deri në tri shkronja të fundit të ndryshme)?

    Lakimi bëhet vetëm mbi rrënjë me të paktën pesë shkronja: "anemisë" përputhet me "anemi", por një rrënjë e
    shkurtër ("gjak") nuk do ta përputhte "Gjakova". Një test kontrollon një listë emrash shembull kundër kësaj.
    """
    folded = fold_token(token)
    if folded in vocabulary():
        return True
    stems = _stems()
    return any(folded[:keep] in stems for keep in range(len(folded), max(len(folded) - 4, 4), -1))


# Skanimi i një vargu

_DASH = r"[\-‐-―−]"
_SEP = rf"\s*[./]\s*|\s*{_DASH}\s*"
_EMAIL = re.compile(r"[^\s@]+@[^\s@]+")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_DATE_DMY = re.compile(rf"(?<!\d)\d{{1,2}}(?:{_SEP})\d{{1,2}}(?:{_SEP})(?:\d{{4}}|\d{{2}})(?!\d)")
_DATE_YMD = re.compile(rf"(?<!\d)\d{{4}}(?:{_SEP})\d{{1,2}}(?:{_SEP})\d{{1,2}}(?!\d)")
_DATE_MY = re.compile(rf"(?<!\d)\d{{1,2}}(?:\s*/\s*|\s*{_DASH}\s*)\d{{4}}(?!\d)")
_PHONE_CLUSTER = re.compile(r"(?<![\d])(?:\+|00)?\(?\d[\d\s().\-/]{5,}\d")
_PLUS_PREFIX = re.compile(r"\+\s*\d{2,}")
_LONG_NUMBER = re.compile(r"\d{4,}")
_NATIONAL_ID = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]\d{8}[A-Za-z](?![A-Za-z0-9])")


def _clean(text: str) -> str:
    """NFKC dhe pa shenja formatimi të padukshme (hapësira me gjerësi zero, shenja të lakimit): një email ose një
    numër nuk duhet të kalojë sepse në mes i është futur një shenjë e padukshme."""
    normalized = unicodedata.normalize("NFKC", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Cf")


def _digits(text: str) -> int:
    return sum(ch.isdigit() for ch in text)


def _has_digit(token: str) -> bool:
    return any(ch.isdigit() for ch in token)


def scan_text(text: str) -> tuple[Kind, ...]:
    """Llojet e të dhënave identifikuese që duken te një varg i lirë; bosh nëse asgjë.

    Funksioni është i pastër dhe nuk kthen vargjet e gjetura. Lista është e renditur dhe pa përsëritje.
    """
    cleaned = _clean(text)
    found: set[Kind] = set()

    if _EMAIL.search(cleaned):
        found.add(Kind.EMAIL)
    if _URL.search(cleaned):
        found.add(Kind.URL)
    if _DATE_DMY.search(cleaned) or _DATE_YMD.search(cleaned) or _DATE_MY.search(cleaned):
        found.add(Kind.DATE)
    if _PLUS_PREFIX.search(cleaned) or any(
        _digits(m.group()) >= 7 for m in _PHONE_CLUSTER.finditer(cleaned)
    ):
        found.add(Kind.PHONE)
    if _LONG_NUMBER.search(cleaned):
        found.add(Kind.LONG_NUMBER)
    if _NATIONAL_ID.search(cleaned):
        found.add(Kind.ID_TOKEN)

    tokens = words(cleaned)
    folded = [fold_token(token) for token, _, _ in tokens]
    for index, (token, _, _) in enumerate(tokens):
        f = folded[index]
        known = is_known_word(token)

        if f in TITLES:
            found.add(Kind.TITLE)
        if f in _ADDRESS_EXACT or f.startswith(_ADDRESS_STEMS):
            found.add(Kind.ADDRESS_CUE)
        if f in _CONTACT_EXACT or f.startswith(_CONTACT_STEMS):
            found.add(Kind.CONTACT_CUE)
        if f.startswith(_BIRTH_STEMS):
            found.add(Kind.BIRTH_OR_AGE)
        if _has_digit(token):
            if not known and any(ch.isalpha() for ch in token) and _digits(token) >= 3:
                found.add(Kind.ID_TOKEN)
            continue
        if token[:1].isupper() and not known:
            found.add(Kind.NAME_LIKE)
        if f.startswith(_MONTHS) and _month_with_number(tokens, index):
            found.add(Kind.DATE)

    return tuple(kind for kind in Kind if kind in found)


def _month_with_number(tokens: list[tuple[str, int, int]], index: int) -> bool:
    """Emri i muajit me një numër pranë (deri në dy fjalë): "12 mars", "mars 2024". Emri i muajit vetëm
    ("kontroll në shtator") nuk identifikon askënd."""
    window = tokens[max(0, index - 2) : index + 3]
    return any(_has_digit(token) for token, _, _ in window)


# Konteksti


@dataclass(frozen=True, slots=True)
class Flag:
    """Një shënim: lloji, fusha e kontekstit dhe indeksi i saj. Nuk mban vargun e shënuar."""

    kind: Kind
    field: str
    index: int


@dataclass(frozen=True, slots=True)
class Verdict:
    flags: tuple[Flag, ...] = ()

    @property
    def clean(self) -> bool:
        return not self.flags

    @property
    def kinds(self) -> tuple[str, ...]:
        """Llojet pa përsëritje, të renditura; ruhen te auditimi dhe te dokumenti."""
        return tuple(sorted({flag.kind.value for flag in self.flags}))


def inspect(context: GroundingContext) -> Verdict:
    """Gjykon çfarë i dërgohet ofruesit për këtë kontekst.

    Kontrollohen të gjitha vargjet që vijnë nga dokumenti dhe hyjnë te kërkesa, dhe vlerat e strukturuara që
    duhet të jenë të katalogut. Gjithçka tjetër te kërkesa është tekst fiks i sistemit ose numër.
    """
    flags: list[Flag] = []

    for index, assertion in enumerate(context.assertions):
        flags.extend(Flag(kind, "assertion", index) for kind in scan_text(assertion.text_span))

    for index, term in enumerate(context.unexplained_terms):
        flags.extend(Flag(kind, "unexplained_term", index) for kind in _scan_unexplained_term(term))

    flags.extend(_check_catalogue(context))
    return Verdict(tuple(flags))


def _scan_unexplained_term(term: str) -> tuple[Kind, ...]:
    """Një term i pashpjeguar duhet të jetë një fjalë e vetme me shkronja të vogla, pa shifra.

    Shkronja e madhe këtu shënohet (`name_like`) edhe kur është thjesht fillim fjalie: termi del nga teksti i lirë,
    jo nga katalogu, dhe një mbiemër që mbaron si term mjekësor ("-uri") do ta kalonte heuristikën e prapashtesave.
    """
    kinds = set(scan_text(term))
    if not re.fullmatch(r"[^\W\d_]{2,40}", term, flags=re.UNICODE):
        kinds.add(Kind.UNCATALOGUED)
    elif term[0].isupper():
        kinds.add(Kind.NAME_LIKE)
    return tuple(kind for kind in Kind if kind in kinds)


def _check_catalogue(context: GroundingContext) -> Iterable[Flag]:
    """Fushat e strukturuara që hyjnë te kërkesa duhet të jenë të katalogut, fjalë për fjalë."""
    analytes = catalog.analytes_by_code()
    for index, finding in enumerate(context.findings):
        analyte = analytes.get(finding.analyte_code)
        if (
            analyte is None
            or finding.analyte_name_canonical != analyte.name_canonical_sq
            or finding.unit_canonical != analyte.unit
        ):
            yield Flag(Kind.UNCATALOGUED, "finding", index)

    terms = catalog.terms_by_name()
    for index, entry in enumerate(context.glossary):
        known = terms.get(entry.term)
        if known is None or entry.explanation_sq != known.explanation_sq:
            yield Flag(Kind.UNCATALOGUED, "glossary", index)
