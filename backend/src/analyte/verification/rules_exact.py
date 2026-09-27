"""
Dega A e verifikimit: rregullat R1-R4.

Këto katër rregulla janë të sakta dhe deterministe. Ato nuk vlerësojnë
kuptim: ato krahasojnë atë që teksti thotë me atë që konteksti përmban,
dhe çdo mospërputhje është shkelje pa shkallë sigurie.

Pikërisht kjo i bën të fuqishme aty ku janë të zbatueshme dhe të verbra
aty ku nuk janë. Një numër i shpikur kapet gjithmonë; një kuptim i
përmbysur nuk i takon kësaj dege.
"""

from __future__ import annotations

from collections.abc import Iterator

from analyte.domain.enums import Direction, Polarity, ViolationType
from analyte.domain.models import GroundingContext, Violation
from analyte.grounding.branch_b.assertions import find_direction
from analyte.grounding.branch_b.negation import polarity_of

from .base import analytes_in, is_attributed, numbers_in, sentences, violation


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
                    f"{code}: pohohet {direction.value}, "
                    f"por statusi i matur është {status.value}",
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
