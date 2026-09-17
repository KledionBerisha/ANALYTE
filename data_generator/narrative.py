"""
Narrativa e mjekut dhe pohimet që ajo përmban.

Ky modul prodhon dy gjëra njëherësh: tekstin e lirë ashtu si do ta
shkruante mjeku, dhe listën e pohimeve me pozicionet e sakta të
karaktereve brenda atij teksti. E dyta është e vërteta bazë e Degës B —
pa të, PK4 nuk matet dot.

Dy vendime formuese:

**Fjalitë janë të shkruara me dorë, jo të përbëra nga fragmente.**
Shqipja ka rasa dhe përshtatje gjinie; një shabllon i tipit
"Vlerat e {emri} janë të rritura" prodhon gjinore të gabuar për gjysmën
e analiteve. Prandaj përdoren vetëm ndërtime ku emri i analitit qëndron
në emërore si kryefjalë, dhe çdo fjali me term mjekësor është shkruar e
plotë me dorë.

**Numrat nuk hyjnë në narrativë.** "Pas tre muajsh" dhe jo "pas 3
muajsh". Një numër i shtypur në narrativë do të hynte më vonë në
bashkësinë e numrave që teksti i gjeneruar mund t'i përmendë, dhe do ta
zbuste pa dashje rregullin R1 pikërisht aty ku ai duhet të jetë i ashpër.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import NamedTuple
from uuid import UUID

from analyte.domain.enums import (
    AnalyteStatus,
    AssertionKind,
    Certainty,
    Direction,
    Polarity,
)
from analyte.domain.models import AnalyteFinding, ReportAssertion

# --------------------------------------------------------------------
# Fjalitë për analitet — emri gjithmonë kryefjalë në emërore
# --------------------------------------------------------------------

OPENINGS: tuple[str, ...] = (
    "Pacienti paraqitet për kontroll rutinë.",
    "Analizat janë kryer me kërkesë të mjekut familjar.",
    "Kontroll periodik i gjendjes së përgjithshme.",
    "Vlerësim laboratorik në kuadër të ndjekjes së rregullt.",
)

Template = tuple[str, str]
"""Një fjali në dy forma: njëjës dhe shumës. Folja shqipe përshtatet me
numrin e kryefjalës, prandaj çdo shabllon shkruhet i dyfishtë."""

ABOVE_TEMPLATES: tuple[Template, ...] = (
    ("{name} rezulton mbi intervalin referent.", "{name} rezultojnë mbi intervalin referent."),
    ("{name} është mbi intervalin referent.", "{name} janë mbi intervalin referent."),
    ("{name} del mbi intervalin referent.", "{name} dalin mbi intervalin referent."),
)

BELOW_TEMPLATES: tuple[Template, ...] = (
    ("{name} rezulton nën intervalin referent.", "{name} rezultojnë nën intervalin referent."),
    ("{name} është nën intervalin referent.", "{name} janë nën intervalin referent."),
    ("{name} del nën intervalin referent.", "{name} dalin nën intervalin referent."),
)

WITHIN_TEMPLATES: tuple[Template, ...] = (
    ("{name} ndodhet brenda intervalit referent.", "{name} ndodhen brenda intervalit referent."),
    (
        "{name} rezulton brenda intervalit referent.",
        "{name} rezultojnë brenda intervalit referent.",
    ),
    ("{name} është brenda kufijve referentë.", "{name} janë brenda kufijve referentë."),
)

HEDGED_ABOVE: tuple[Template, ...] = (
    (
        "{name} duket mbi intervalin referent, por kërkon rikontroll.",
        "{name} duken mbi intervalin referent, por kërkojnë rikontroll.",
    ),
    ("{name} mund të jetë mbi intervalin referent.", "{name} mund të jenë mbi intervalin referent."),
)

HEDGED_BELOW: tuple[Template, ...] = (
    (
        "{name} duket nën intervalin referent, por kërkon rikontroll.",
        "{name} duken nën intervalin referent, por kërkojnë rikontroll.",
    ),
    ("{name} mund të jetë nën intervalin referent.", "{name} mund të jenë nën intervalin referent."),
)

NEGATED_ABOVE: tuple[Template, ...] = (
    ("{name} nuk rezulton mbi intervalin referent.", "{name} nuk rezultojnë mbi intervalin referent."),
    ("{name} nuk del mbi intervalin referent.", "{name} nuk dalin mbi intervalin referent."),
)

NEGATED_BELOW: tuple[Template, ...] = (
    ("{name} nuk rezulton nën intervalin referent.", "{name} nuk rezultojnë nën intervalin referent."),
    ("{name} nuk del nën intervalin referent.", "{name} nuk dalin nën intervalin referent."),
)

RECOMMENDATIONS: tuple[str, ...] = (
    "Rekomandohet kontroll pas tre muajsh.",
    "Rekomandohet përsëritja e analizave pas një muaji.",
    "Rekomandohet konsultë me mjekun specialist.",
    "Rekomandohet ndjekje e mëtejshme e vlerave.",
    "Rekomandohet vlerësim klinik i mëtejshëm.",
)


# --------------------------------------------------------------------
# Fjalitë me terma mjekësorë
# --------------------------------------------------------------------


class Name(NamedTuple):
    """Emri i analitit në narrativë bashkë me numrin e tij gramatikor."""

    text: str
    plural: bool


def _render(rng: random.Random, templates: tuple[Template, ...], name: Name) -> str:
    return rng.choice(templates)[1 if name.plural else 0].format(name=name.text)


class Condition(NamedTuple):
    """Kushti klinik nën të cilin një fjali me term ka kuptim."""

    analyte_code: str
    statuses: frozenset[AnalyteStatus]


def _cond(code: str, *statuses: AnalyteStatus) -> Condition:
    return Condition(code, frozenset(statuses))


ABNORMAL_HIGH = (AnalyteStatus.HIGH, AnalyteStatus.CRITICAL_HIGH)
ABNORMAL_LOW = (AnalyteStatus.LOW, AnalyteStatus.CRITICAL_LOW)


@dataclass(frozen=True, slots=True)
class TermSentence:
    """Fjali e shkruar me dorë që përmend një term mjekësor.

    `requires_any` e lidh fjalinë me gjendjen e matur: një narrativë që
    përmend leukocitozë kur leukocitet janë normale do të ishte korpus i
    pakujdesshëm, jo korpus i vështirë. Fjalitë pa kusht janë të
    përgjithshme dhe vlejnë gjithmonë.
    """

    term: str
    text: str
    polarity: Polarity
    certainty: Certainty
    requires_any: tuple[Condition, ...] = ()

    def is_eligible(self, statuses: dict[str, AnalyteStatus]) -> bool:
        if not self.requires_any:
            return True
        return any(statuses.get(c.analyte_code) in c.statuses for c in self.requires_any)


# Terma që gjenden në resources/terminology.csv — shpjegohen (Dega B).
EXPLAINED_TERM_SENTENCES: tuple[TermSentence, ...] = (
    TermSentence(
        "anemi",
        "Nuk ka shenja të anemisë.",
        Polarity.NEGATED,
        Certainty.CONFIRMED,
        (_cond("718-7", AnalyteStatus.NORMAL, *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "anemi",
        "Vërehet anemi e shkallës së lehtë.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("718-7", *ABNORMAL_LOW),),
    ),
    TermSentence(
        "leukocitozë",
        "Vërehet leukocitozë.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("6690-2", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "leukopeni",
        "Vërehet leukopeni.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("6690-2", *ABNORMAL_LOW),),
    ),
    TermSentence(
        "trombocitopeni",
        "Vërehet trombocitopeni.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("777-3", *ABNORMAL_LOW),),
    ),
    TermSentence(
        "hiperglicemi",
        "Vërehet hiperglicemi.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("2345-7", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "hipoglicemi",
        "Vërehet hipoglicemi.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("2345-7", *ABNORMAL_LOW),),
    ),
    TermSentence(
        "hiperkalemi",
        "Vërehet hiperkalemi.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("2823-3", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "hipokalemi",
        "Vërehet hipokalemi.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("2823-3", *ABNORMAL_LOW),),
    ),
    TermSentence(
        "hiperurikemi",
        "Vërehet hiperurikemi.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("3084-1", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "azotemi",
        "Vërehet azotemi e lehtë.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("3094-0", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "dislipidemi",
        "Vlerat mund të tregojnë dislipidemi.",
        Polarity.AFFIRMED,
        Certainty.HEDGED,
        (_cond("2093-3", *ABNORMAL_HIGH), _cond("2571-8", *ABNORMAL_HIGH)),
    ),
    TermSentence(
        "sideropeni",
        "Nuk përjashtohet sideropeni.",
        Polarity.AFFIRMED,
        Certainty.HEDGED,
        (_cond("2276-4", *ABNORMAL_LOW), _cond("2498-4", *ABNORMAL_LOW)),
    ),
    TermSentence(
        "hipotiroidizëm",
        "Nuk përjashtohet hipotiroidizëm.",
        Polarity.AFFIRMED,
        Certainty.HEDGED,
        (_cond("3016-3", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "hipertiroidizëm",
        "Nuk përjashtohet hipertiroidizëm.",
        Polarity.AFFIRMED,
        Certainty.HEDGED,
        (_cond("3016-3", *ABNORMAL_LOW),),
    ),
    TermSentence(
        "steatozë",
        "Vlerat sugjerojnë steatozë hepatike.",
        Polarity.AFFIRMED,
        Certainty.HEDGED,
        (_cond("1742-6", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "inflamacion",
        "Vërehen shenja inflamacioni.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("1988-5", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "inflamacion",
        "Nuk ka shenja inflamacioni.",
        Polarity.NEGATED,
        Certainty.CONFIRMED,
        (_cond("1988-5", AnalyteStatus.NORMAL),),
    ),
    TermSentence("hemolizë", "Nuk vërehen shenja të hemolizës.", Polarity.NEGATED, Certainty.CONFIRMED),
    TermSentence(
        "eritropoezë",
        "Vlerësohet gjendja e përgjithshme e eritropoezës.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
    ),
    TermSentence(
        "funksioni hepatik",
        "Funksioni hepatik është vlerësuar në tërësi.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
    ),
    TermSentence(
        "funksioni renal",
        "Funksioni renal është vlerësuar në tërësi.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
    ),
)

# Terma që NUK gjenden në tabelë — sistemi duhet t'i lërë të pashpjeguar (SP6).
UNEXPLAINED_TERM_SENTENCES: tuple[TermSentence, ...] = (
    TermSentence(
        "makrocitozë",
        "Vërehet makrocitozë e lehtë.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("787-2", *ABNORMAL_HIGH),),
    ),
    TermSentence(
        "mikrocitozë",
        "Vërehet mikrocitozë e lehtë.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("787-2", *ABNORMAL_LOW),),
    ),
    TermSentence(
        "hipokromi",
        "Vërehet hipokromi e lehtë.",
        Polarity.AFFIRMED,
        Certainty.CONFIRMED,
        (_cond("785-6", *ABNORMAL_LOW),),
    ),
    TermSentence("anizocitozë", "Vërehet anizocitozë e lehtë.", Polarity.AFFIRMED, Certainty.CONFIRMED),
    TermSentence("eozinofili", "Vërehet eozinofili e lehtë.", Polarity.AFFIRMED, Certainty.CONFIRMED),
    TermSentence("monocitozë", "Vërehet monocitozë e lehtë.", Polarity.AFFIRMED, Certainty.CONFIRMED),
    TermSentence("retikulocitozë", "Vërehet retikulocitozë e lehtë.", Polarity.AFFIRMED, Certainty.CONFIRMED),
)


# --------------------------------------------------------------------
# Ndërtimi
# --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Narrative:
    """Teksti i mjekut bashkë me të vërtetën bazë të tij."""

    text: str
    assertions: tuple[ReportAssertion, ...]
    explained_terms: tuple[str, ...]
    unexplained_terms: tuple[str, ...]


class _Planned(NamedTuple):
    """Një fjali e planifikuar përpara se të njihen pozicionet."""

    text: str
    analyte_code: str | None
    direction: Direction
    polarity: Polarity
    certainty: Certainty
    kind: AssertionKind
    is_assertion: bool


def _plain(text: str) -> _Planned:
    return _Planned(
        text, None, Direction.UNSPECIFIED, Polarity.AFFIRMED,
        Certainty.CONFIRMED, AssertionKind.FINDING, is_assertion=False,
    )


def build_narrative(
    rng: random.Random,
    findings: tuple[AnalyteFinding, ...],
    display_names: dict[str, Name],
    unmeasured: tuple[tuple[str, Name], ...],
    new_id: Callable[[], UUID],
) -> Narrative:
    """Ndërton narrativën dhe pohimet e saj.

    `unmeasured` janë çiftet (kod, emër) të analiteve që mjeku mund t'i
    përmendë pa qenë të matura në këtë dokument — burimi i gjendjes
    MENTIONED_NOT_MEASURED, që një lexues njerëzor rrallë e vëren.
    """
    statuses = {f.analyte_code: f.status for f in findings}
    used: set[str] = set()
    planned: list[_Planned] = [_plain(rng.choice(OPENINGS))]

    interpretable = [f for f in findings if f.status is not AnalyteStatus.UNINTERPRETABLE]
    abnormal = [f for f in interpretable if f.status.is_abnormal]
    normal = [f for f in interpretable if f.status is AnalyteStatus.NORMAL]

    # 1. Gjetjet jonormale të pohuara saktë — gjendja AGREEMENT.
    for finding in _take(rng, abnormal, rng.randint(1, 3), used):
        planned.append(_directional(rng, finding, display_names, agree=True))

    # 2. Një mospërputhje: mjeku e quan normale një vlerë jashtë intervalit.
    #    Kjo është gjendja CONTRADICTION dhe ndodh edhe në raporte reale.
    if abnormal and rng.random() < 0.25:
        for finding in _take(rng, abnormal, 1, used):
            if rng.random() < 0.5:
                # Drejtim i kundërt me matjen.
                planned.append(_directional(rng, finding, display_names, agree=False))
            else:
                # E quan normale një vlerë jashtë intervalit.
                planned.append(
                    _assertion(
                        _render(rng, WITHIN_TEMPLATES, display_names[finding.analyte_code]),
                        finding.analyte_code,
                        Direction.NORMAL,
                        Polarity.AFFIRMED,
                        Certainty.CONFIRMED,
                    )
                )

    # 3. Mohim mbi një vlerë normale — lënda e rregullit R5.
    if normal and rng.random() < 0.35:
        for finding in _take(rng, normal, 1, used):
            name = display_names[finding.analyte_code]
            above = rng.random() < 0.5
            templates = NEGATED_ABOVE if above else NEGATED_BELOW
            planned.append(
                _assertion(
                    _render(rng, templates, name),
                    finding.analyte_code,
                    Direction.INCREASED if above else Direction.DECREASED,
                    Polarity.NEGATED,
                    Certainty.CONFIRMED,
                )
            )

    # 4. Pohim me pasiguri — lënda e rregullit R6.
    if abnormal and rng.random() < 0.35:
        for finding in _take(rng, abnormal, 1, used):
            planned.append(_directional(rng, finding, display_names, agree=True, hedged=True))

    # 5. Analit i përmendur por i pamatur.
    if unmeasured and rng.random() < 0.30:
        code, name = rng.choice(unmeasured)
        if code not in used:
            used.add(code)
            above = rng.random() < 0.5
            templates = ABOVE_TEMPLATES if above else BELOW_TEMPLATES
            planned.append(
                _assertion(
                    _render(rng, templates, name),
                    code,
                    Direction.INCREASED if above else Direction.DECREASED,
                    Polarity.AFFIRMED,
                    Certainty.CONFIRMED,
                )
            )

    # 6. Fjalitë me terma.
    explained, unexplained = [], []
    for sentence in _pick_terms(rng, EXPLAINED_TERM_SENTENCES, statuses, rng.randint(0, 2)):
        explained.append(sentence.term)
        planned.append(_term_assertion(sentence))
    for sentence in _pick_terms(rng, UNEXPLAINED_TERM_SENTENCES, statuses, rng.randint(0, 1)):
        unexplained.append(sentence.term)
        planned.append(_term_assertion(sentence))

    # 7. Rekomandimet — lënda e rregullit R8.
    for text in rng.sample(RECOMMENDATIONS, k=1 if rng.random() < 0.8 else 2):
        planned.append(
            _assertion(text, None, Direction.UNSPECIFIED, Polarity.AFFIRMED,
                       Certainty.CONFIRMED, kind=AssertionKind.RECOMMENDATION)
        )

    return _assemble(planned, new_id, tuple(explained), tuple(unexplained))


def _assemble(
    planned: list[_Planned],
    new_id: Callable[[], UUID],
    explained: tuple[str, ...],
    unexplained: tuple[str, ...],
) -> Narrative:
    """Bashkon fjalitë dhe llogarit pozicionet e sakta.

    Hapësira e ndarjes shtohet ndërmjet fjalive, prandaj fillimi i çdo
    fjalie është shuma e gjatësive të mëparshme plus ndarësit. Pika
    përfundimtare mbetet jashtë spanit: ajo i përket fjalisë, jo pohimit.
    """
    text_parts = [p.text for p in planned]
    text = " ".join(text_parts)

    assertions: list[ReportAssertion] = []
    offset = 0
    for part in planned:
        if part.is_assertion:
            span = part.text.rstrip(".")
            assertions.append(
                ReportAssertion(
                    id=new_id(),
                    text_span=span,
                    analyte_code=part.analyte_code,
                    direction=part.direction,
                    polarity=part.polarity,
                    certainty=part.certainty,
                    kind=part.kind,
                    char_start=offset,
                    char_end=offset + len(span),
                )
            )
        offset += len(part.text) + 1  # +1 për hapësirën ndarëse

    return Narrative(text, tuple(assertions), explained, unexplained)


def _assertion(
    text: str,
    analyte_code: str | None,
    direction: Direction,
    polarity: Polarity,
    certainty: Certainty,
    kind: AssertionKind = AssertionKind.FINDING,
) -> _Planned:
    return _Planned(text, analyte_code, direction, polarity, certainty, kind, is_assertion=True)


def _term_assertion(sentence: TermSentence) -> _Planned:
    return _Planned(
        sentence.text,
        None,
        Direction.UNSPECIFIED,
        sentence.polarity,
        sentence.certainty,
        AssertionKind.TERM_MENTION,
        is_assertion=True,
    )


def _directional(
    rng: random.Random,
    finding: AnalyteFinding,
    display_names: dict[str, Name],
    *,
    agree: bool,
    hedged: bool = False,
) -> _Planned:
    """Fjali që pohon drejtimin e një gjetjeje.

    Me `agree=True` drejtimi i pohuar është ai i statusit të matur; kjo
    prodhon AGREEMENT. Pa të, drejtimi kthehet përmbys dhe prodhon
    CONTRADICTION.
    """
    direction = finding.status.direction
    if not agree:
        direction = (
            Direction.DECREASED if direction is Direction.INCREASED else Direction.INCREASED
        )

    name = display_names[finding.analyte_code]
    if direction is Direction.INCREASED:
        templates = HEDGED_ABOVE if hedged else ABOVE_TEMPLATES
    elif direction is Direction.DECREASED:
        templates = HEDGED_BELOW if hedged else BELOW_TEMPLATES
    else:
        templates = WITHIN_TEMPLATES

    return _assertion(
        _render(rng, templates, name),
        finding.analyte_code,
        direction,
        Polarity.AFFIRMED,
        Certainty.HEDGED if hedged else Certainty.CONFIRMED,
    )


def _take(
    rng: random.Random, pool: list[AnalyteFinding], count: int, used: set[str]
) -> list[AnalyteFinding]:
    """Zgjedh gjetje të papërdorura më parë.

    Një analit i vetëm nuk duhet të marrë dy pohime: krahasimi i
    kryqëzuar është një gjendje për analit, prandaj dy pohime për të
    njëjtin analit do ta bënin të vërtetën bazë të dykuptimtë.
    """
    available = [f for f in pool if f.analyte_code not in used]
    picked = available[:count] if count >= len(available) else rng.sample(available, k=count)
    for finding in picked:
        used.add(finding.analyte_code)
    return picked


def _pick_terms(
    rng: random.Random,
    pool: tuple[TermSentence, ...],
    statuses: dict[str, AnalyteStatus],
    count: int,
) -> list[TermSentence]:
    """Fjalitë me term që përputhen me gjendjen e matur, pa përsëritje termi."""
    if count <= 0:
        return []
    eligible = [s for s in pool if s.is_eligible(statuses)]
    picked: list[TermSentence] = []
    seen: set[str] = set()
    for sentence in rng.sample(eligible, k=min(count, len(eligible))):
        if sentence.term in seen:
            continue
        seen.add(sentence.term)
        picked.append(sentence)
    return picked
