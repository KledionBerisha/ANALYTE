"""
Dega A e verifikimit: rregullat R1-R4.

"""

from __future__ import annotations

import re
from collections.abc import Iterator

from analyte.domain.enums import AnalyteStatus, Direction, Polarity, ViolationType
from analyte.domain.models import GroundingContext, Violation
from analyte.grounding.branch_b.assertions import find_direction
from analyte.grounding.branch_b.negation import polarity_of
from analyte.textnorm import fold

from . import ruleset
from .base import analytes_in, is_attributed, numbers_in, sentences, violation, without_glosses


def check_numbers(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R1 — çdo numër duhet të gjendet ndër numrat e mbështetur.

    Bashkësia e lejuar përmban vlerën e matur, vlerën e normalizuar dhe të
    dy kufijtë e intervalit për çdo gjetje. Intervali është aty me qëllim:
    pacienti duhet të mund ta shohë krahas vlerës.

    Fjalitë e atribuuara kanë burim tjetër (ADR 0010): numri në "kontroll
    pas 3 muajsh" është i mjekut dhe verifikohet kundrejt pohimeve të tij,
    jo kundrejt matjeve. Përjashtimi nuk shtrihet te fjalitë e sistemit —
    aty e njëjta "3" do të ishte numër i shpikur.
    """
    measured = context.all_grounded_numbers()
    quoted = measured | {
        value
        for assertion in context.assertions
        for value, _ in numbers_in(assertion.text_span, context)
    }
    for sentence in sentences(text):
        allowed = quoted if is_attributed(sentence.text) else measured
        for value, raw in numbers_in(sentence.text, context):
            if value not in allowed:
                yield violation(
                    ViolationType.UNGROUNDED_NUMBER,
                    sentence.text,
                    f"numri {raw} nuk gjendet ndër vlerat e nxjerra",
                )
    if ruleset.modern():
        yield from _misattributed_numbers(context, text)


def _misattributed_numbers(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R1 (`r1.4`) — numri duhet t'i përkasë analitit për të cilin flet fjalia.

    Auditi i E8 gjeti vlera të vendosura te analiti tjetër ("37,4 brenda 32–36" kur 37,4 ishte vlera e një analiti dhe 32–36
    kufiri i tjetrit). R1 e pranon numrin sepse ai ekziston diku te konteksti. Kontrolli është i ngushtë me qëllim: vetëm te
    fjalitë që përmendin NJË analit të vetëm, ku përkatësia është e padyshimtë; një fjali me dy analite mund ta ndajë numrat
    në çdo mënyrë dhe nuk gjykohet këtu.
    """
    by_code = {finding.analyte_code: finding for finding in context.findings}
    for sentence in sentences(text):
        if is_attributed(sentence.text):
            continue
        codes = analytes_in(without_glosses(sentence.text, context), context)
        if len(codes) != 1 or codes[0] not in by_code:
            continue
        own = by_code[codes[0]].grounded_numbers()
        others: set = set()
        for code, finding in by_code.items():
            if code != codes[0]:
                others |= finding.grounded_numbers()
        for value, raw in numbers_in(sentence.text, context):
            if value in others and value not in own:
                yield violation(
                    ViolationType.UNGROUNDED_NUMBER,
                    sentence.text,
                    f"numri {raw} është vlerë ose kufi i një analiti tjetër, jo i {codes[0]}",
                )


def check_analytes(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R2 — çdo analit i përmendur duhet të jetë ndër ata të matur."""
    # Analiti që mjeku e ka përmendur është i mbështetur edhe kur nuk është
    # matur: dalja ka të drejtë ta citojë atë. Rasti "i përmendur por i
    # pamatur" regjistrohet nga krahasimi i kryqëzuar, jo nga ky rregull.
    known = context.known_analyte_codes() | {
        assertion.analyte_code
        for assertion in context.assertions
        if assertion.analyte_code is not None
    }
    # Termi i fjalorit hyn në kontekst sepse raporti e përmendi, dhe
    # shpjegimi i tij vjen nga tabela; të dy mund të emërtojnë një analit pa
    # e pretenduar si të matur. "Qelizat e kuqe" brenda shpjegimit të
    # hemoglobinës është variant i eritrociteve. R7 i pranon termat e
    # shpjegimeve për të njëjtën arsye.
    for entry in context.glossary:
        known |= set(analytes_in(f"{entry.term}. {entry.explanation_sq}", context))
    for sentence in sentences(text):
        for code in analytes_in(sentence.text, context):
            if code not in known:
                yield violation(
                    ViolationType.UNGROUNDED_ANALYTE,
                    sentence.text,
                    f"analiti {code} nuk është matur në këtë dokument",
                )


def check_direction(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R3 — drejtimi i pohuar duhet të përputhet me statusin e klasifikuar.

    Mohimi trajtohet veçmas: "nuk është mbi intervalin" nuk pretendon se
    vlera është e ulët, prandaj ai përputhet me çdo status që nuk është i
    rritur dhe nuk krahasohet drejtpërdrejt me statusin.
    """
    if ruleset.modern():
        yield from _direction_by_clause(context, text)
        yield from _blanket_claims(context, text)
        return
    for sentence in sentences(text):
        if is_attributed(sentence.text):
            # Citimi i mjekut gjykohet kundrejt burimit nga R5, jo kundrejt
            # matjes. Një mjek që e ka gabim nuk është gabim i sistemit.
            continue
        direction = find_direction(sentence.text)
        if direction is Direction.UNSPECIFIED:
            continue
        negated = polarity_of(sentence.text) is Polarity.NEGATED

        for code in analytes_in(sentence.text, context):
            status = context.status_of(code)
            if status is None:
                continue  # R2 e mbulon këtë rast
            expected = status.direction
            if negated:
                if expected is direction:
                    yield violation(
                        ViolationType.DIRECTION_MISMATCH,
                        sentence.text,
                        f"{code}: mohohet drejtimi {direction.value}, "
                        f"por statusi i matur është {status.value}",
                    )
            elif expected is not direction:
                yield violation(
                    ViolationType.DIRECTION_MISMATCH,
                    sentence.text,
                    f"{code}: pohohet {direction.value}, por statusi i matur është {status.value}",
                )


def check_critical_coverage(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R4 — çdo gjetje kritike duhet të shfaqet në dalje.

    Ky rregull nuk vendoset nga një fjali: mungesa e diçkaje nuk shihet
    duke lexuar një fjali, prandaj ai shqyrton tërë daljen. E njëjta veti
    do të thotë se ai nuk mund të mësohet nga një klasifikues fjalie —
    dallim që hyn drejtpërdrejt në diskutimin e PK6.
    """
    mentioned = set(analytes_in(text, context))
    for finding in context.critical_findings():
        if finding.analyte_code not in mentioned:
            yield violation(
                ViolationType.MISSING_CRITICAL,
                "",
                f"gjetja kritike {finding.analyte_name_canonical} "
                f"({finding.analyte_code}) nuk përmendet në dalje",
            )


# r1.4 — R3 sipas klauzolës, dhe pohimet e përgjithshme

_CONTRAST = re.compile(
    r";|\s+ndërsa\s+|\s+ndersa\s+|\s+por\s+|\s+ndërkohë\s+që\s+|\s+ndërkohë\s+|\s+ndërkohe\s+",
    re.IGNORECASE,
)
_COORDINATION = re.compile(r"\s+dhe\s+", re.IGNORECASE)


def _compare(
    context: GroundingContext, codes: list[str], direction: Direction, negated: bool, sentence: str
) -> Iterator[Violation]:
    for code in codes:
        status = context.status_of(code)
        if status is None:
            continue  # R2 e mbulon këtë rast
        expected = status.direction
        if negated:
            if expected is direction:
                yield violation(
                    ViolationType.DIRECTION_MISMATCH,
                    sentence,
                    f"{code}: mohohet drejtimi {direction.value}, por statusi i matur është {status.value}",
                )
        elif expected is not direction:
            yield violation(
                ViolationType.DIRECTION_MISMATCH,
                sentence,
                f"{code}: pohohet {direction.value}, por statusi i matur është {status.value}",
            )


def _direction_by_clause(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R3 (`r1.4`) — një drejtim për çdo analit, jo një për tërë fjalinë.

    r1.3 e krahasonte drejtimin e parë të fjalisë me çdo analit të përmendur në të, kështu që "Kalciumi është i ulët dhe
    kreatinina e lartë" jepte alarm të rremë, dhe fjalori i drejtimit nuk njihte "të larta" apo "rritja e". Tani fjalia ndahet
    te kundërvënia (`;`, "ndërsa", "por") në pjesë të pavarura, dhe pjesa te "dhe" në klauzola: një klauzolë që ka analit dhe
    drejtim gjykohet vetvetiu; një klauzolë me analit e pa drejtim e jep analitin te klauzola pasardhëse VETËM kur ajo nuk
    përmend analit tjetër ("Hb është 15,5 dhe bie brenda 13,5–17,5"). Mohimi gjykohet po për klauzolë.
    """
    for sentence in sentences(text):
        if is_attributed(sentence.text):
            continue
        for segment in _CONTRAST.split(without_glosses(sentence.text, context)):
            pending: list[str] = []
            for clause in _COORDINATION.split(segment):
                codes = analytes_in(clause, context)
                direction = find_direction(clause, extended=True)
                if codes and direction is not Direction.UNSPECIFIED:
                    negated = polarity_of(clause) is Polarity.NEGATED
                    yield from _compare(context, codes, direction, negated, sentence.text)
                    pending = []
                elif codes:
                    pending = codes
                elif direction is not Direction.UNSPECIFIED and pending:
                    negated = polarity_of(clause) is Polarity.NEGATED
                    yield from _compare(context, pending, direction, negated, sentence.text)
                    pending = []


_BLANKET_QUANTIFIERS = ("te gjitha", "gjitha", "gjithe", "cdo vlere", "pjesa tjeter", "te tjerat")
"""Sasiorë TOTALË. "Në analizat e tjera, natriumi është 142 ..." nuk është pohim i përgjithshëm: ai emërton një analit;
vetëm "të gjitha", "gjithë", "pjesa tjetër", "të tjerat" pretendojnë çdo gjetje."""
_BLANKET_OTHERS = ("tjera", "tjere", "tjerat", "tjeter", "tjetra")
_ABNORMAL = {
    AnalyteStatus.HIGH,
    AnalyteStatus.LOW,
    AnalyteStatus.CRITICAL_HIGH,
    AnalyteStatus.CRITICAL_LOW,
}


def _blanket_claims(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R3 (`r1.4`) — "të gjitha vlerat e tjera janë brenda intervalit" është pohim për çdo gjetje që nuk u përmend.

    Auditi i E8 gjeti këtë forma si burimin kryesor të drejtimeve të gabuara që rregullat nuk i shihnin (21 nga 90 tekste):
    asnjë analit i emëruar nuk është i gabuar, por pohimi i përgjithshëm është i rremë kur një gjetje jashtë intervalit nuk
    është përmendur. Shkelja kërkon një sasior ("të gjitha", "vlerat e tjera") dhe një shenjë normaliteti. Kur fjalia thotë
    "të tjera", gjetjet e përmendura më parë (ose në të njëjtën fjali) përjashtohen; pa të, çdo gjetje jashtë intervalit e
    kundërshton pohimin.
    """
    abnormal = {f.analyte_code: f for f in context.findings if f.status in _ABNORMAL}
    if not abnormal:
        return
    seen: set[str] = set()
    for sentence in sentences(text):
        here = set(analytes_in(sentence.text, context))
        folded = fold(sentence.text)
        padded = f" {folded} "
        blanket = any(f" {q} " in padded for q in _BLANKET_QUANTIFIERS)
        if (
            blanket
            and not is_attributed(sentence.text)
            and find_direction(sentence.text, extended=True) is Direction.NORMAL
            and polarity_of(sentence.text) is not Polarity.NEGATED
        ):
            says_others = any(f" {o} " in padded for o in _BLANKET_OTHERS)
            uncovered = [c for c in abnormal if not says_others or c not in (seen | here)]
            if uncovered:
                yield violation(
                    ViolationType.DIRECTION_MISMATCH,
                    sentence.text,
                    f"pohim i përgjithshëm që ka një gjetje jashtë intervalit ({uncovered[0]}) që nuk përjashtohet",
                )
        seen |= here
