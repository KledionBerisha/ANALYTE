"""
Njohja e termave mjekësorë në tekstin e mjekut.

"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import lru_cache

from analyte.catalog import Term, load_terminology
from analyte.domain.models import GlossaryEntry
from analyte.textnorm import fold_token, words

MIN_PREFIX_MATCH = 4
"""Nën këtë gjatësi kërkohet përputhje e plotë. Një term trishkronjësh i
përputhur si parashtesë do të kapte gjysmën e fjalorit."""

MIN_UNKNOWN_LENGTH = 7
"""Fjalët e shkurtra nuk konsiderohen kurrë terma mjekësorë të panjohur."""

MEDICAL_SUFFIXES: tuple[str, ...] = (
    "oze",
    "ozes",
    "emia",
    "emi",
    "penia",
    "peni",
    "uria",
    "uri",
    "filia",
    "fili",
    "kromi",
    "patia",
    "pati",
)
"""Prapashtesat që tregojnë term mjekësor.

Lista është e shkurtër me qëllim: çdo shtesë rrit mbulimin dhe ul
saktësinë, dhe ky shkëmbim duhet bërë me matje e jo me ndjesi. "-itet"
ishte këtu dhe u hoq: ai kap "paraqitet", një folje e zakonshme, dhe
prodhonte një term të pashpjeguar në pothuajse çdo dokument."""

FALSE_FRIENDS: frozenset[str] = frozenset(
    {"profili", "sistemi", "problemi", "materiali", "protokolli", "rezultati"}
)
"""Fjalë të zakonshme që mbarojnë si terma mjekësorë pa qenë të tilla.

Lista shmang shpikjen e një rregulli morfologjik më të hollë për të cilin
nuk ka as të dhëna e as nevojë; kur ajo të rritet përtej disa dhjetësh,
do të thotë se heuristika e prapashtesave ka dalë nga fuqia e vet."""


@dataclass(frozen=True, slots=True)
class TermMatch:
    """Një term i gjetur në tekst, me vendin ku u gjet."""

    term: Term
    surface: str
    start: int
    end: int


@lru_cache(maxsize=1)
def _forms() -> tuple[tuple[tuple[str, ...], Term], ...]:
    """Format e kërkimit: çdo term dhe sinonim, i ndarë në fjalë.

    Renditen nga më e gjata te më e shkurtra, që "HDL-kolesteroli" të mos
    kapet si "kolesterol" kur të dyja janë në tabelë.
    """
    forms: list[tuple[tuple[str, ...], Term]] = []
    for entry in load_terminology():
        for surface in entry.surface_forms():
            tokens = tuple(fold_token(part) for part in surface.split() if part.strip())
            if tokens:
                forms.append((tokens, entry))
    return tuple(sorted(forms, key=lambda item: -len(item[0])))


def detect_terms(text: str) -> tuple[TermMatch, ...]:
    """Termat e tabelës që shfaqen në tekst, pa përsëritje mbivendosjeje."""
    tokens = words(text)
    folded = [fold_token(token) for token, _, _ in tokens]

    matches: list[TermMatch] = []
    taken: set[int] = set()

    for form, entry in _forms():
        size = len(form)
        for index in range(len(folded) - size + 1):
            if any(position in taken for position in range(index, index + size)):
                continue
            if _matches(folded[index : index + size], form):
                start = tokens[index][1]
                end = tokens[index + size - 1][2]
                matches.append(TermMatch(entry, text[start:end], start, end))
                taken.update(range(index, index + size))

    return tuple(sorted(matches, key=lambda match: match.start))


def _matches(candidate: list[str], form: tuple[str, ...]) -> bool:
    """Çdo fjalë e termit lejohet me prapashtesë, jo vetëm e fundit.

    Shqipja e lakon edhe kryefjalën e një termi me dy fjalë: "interval
    referent" shfaqet si "intervalin referent". Nëse toleranca do të
    vlente vetëm për fjalën e fundit, termat shumëfjalësh do të gjendeshin
    pothuajse kurrë — dhe mungesa e tyre në fjalor do të dukej si vendim i
    tabelës e jo si dobësi e përputhjes.
    """
    return all(
        _token_matches(actual, expected) for actual, expected in zip(candidate, form, strict=True)
    )


def _token_matches(actual: str, expected: str) -> bool:
    if len(expected) < MIN_PREFIX_MATCH:
        return actual == expected
    return actual.startswith(expected)


def glossary_for(text: str) -> tuple[GlossaryEntry, ...]:
    """Zërat e fjalorit për termat e përmendur në tekst.

    Vetëm termat që janë vërtet në tabelë përfundojnë këtu. Kjo është ana
    e dukshme e SP6: çdo shpjegim që del te pacienti ka një burim të
    regjistruar pas vetes.
    """
    seen: dict[str, Term] = {}
    for match in detect_terms(text):
        seen.setdefault(match.term.term, match.term)

    return tuple(
        GlossaryEntry(
            term=entry.term,
            explanation_sq=entry.explanation_sq,
            source_ref=entry.source_ref,
            category=entry.category,
            synonyms=entry.synonyms,
        )
        for entry in seen.values()
    )


def detect_unknown_terms(text: str, is_known: Callable[[str], bool]) -> tuple[str, ...]:
    """Fjalë me trajtë mjekësore që sistemi nuk i njeh (SP6).

    `is_known` vendos çfarë përjashtohet: termat e tabelës dhe emrat e
    analiteve. Pa të, "Glukoza" do të raportohej si term i pashpjeguar
    vetëm sepse mbaron me -oza, ndërsa ajo trajtohet nga Dega A.

    Kthehet forma e shtypur dhe jo ajo e normalizuar: teksti që i shfaqet
    pacientit duhet ta përmendë termin ashtu si e shkroi mjeku.
    """
    found: dict[str, str] = {}
    for token, _, _ in words(text):
        folded = fold_token(token)
        if len(folded) < MIN_UNKNOWN_LENGTH:
            continue
        if not folded.endswith(MEDICAL_SUFFIXES):
            continue
        if folded in FALSE_FRIENDS:
            continue
        if is_known(token):
            continue
        found.setdefault(folded, token)
    return tuple(found.values())


def known_term_predicate() -> Callable[[str], bool]:
    """Kthen një provë përkatësie vetëm ndaj tabelës terminologjike."""

    def is_known(token: str) -> bool:
        return bool(detect_terms(token))

    return is_known


def any_of(predicates: Iterable[Callable[[str], bool]]) -> Callable[[str], bool]:
    """Bashkon disa prova përkatësie në një."""
    collected = tuple(predicates)

    def is_known(token: str) -> bool:
        return any(predicate(token) for predicate in collected)

    return is_known
