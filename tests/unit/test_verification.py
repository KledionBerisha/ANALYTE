"""
Testet e shabllonit dhe të shtresës së verifikimit.

Dy pohime mbajnë gjithçka këtu.

**Shablloni duhet të kalojë çdo rregull.** Ai ndërtohet vetëm nga
konteksti, prandaj një shkelje mbi të nuk është gabim i tij por i
rregullit që e raportoi. Ky test është i vetmi që dallon një rregull të
ashpër nga një rregull i gabuar.

**Çdo rregull duhet të kapë defektin e vet.** Defektet injektohen me dorë
te teksti i pastër, një nga një, dhe rregulli përkatës duhet ta shohë
secilin.
"""

import random

import pytest

from analyte.domain.enums import ViolationType
from analyte.domain.policy import (
    ATTRIBUTION_PREFIX_SQ,
    CRITICAL_BANNER_SQ,
    DISCLAIMER_SQ,
)
from analyte.generation.templates import build
from analyte.verification.base import is_attributed, numbers_in, sentences
from analyte.verification.pipeline import RULES, verify
from data_generator.ground_truth import build_document
from data_generator.ids import IdFactory


def _document(seed: str):
    rng = random.Random(seed)
    return build_document(rng, IdFactory(rng), scanned_share=0.0)


@pytest.fixture(scope="module")
def documents():
    return [_document(f"ver{i}") for i in range(12)]


# --------------------------------------------------------------------
# Shablloni
# --------------------------------------------------------------------


def test_template_passes_every_rule(documents):
    """Dalja e ndërtuar vetëm nga konteksti nuk mund të jetë e pambështetur."""
    for document in documents:
        result = verify(document.context, build(document.context))
        assert result.passed, [
            (v.type.value, v.evidence) for v in result.violations
        ]


def test_template_carries_the_disclaimer(documents):
    """SP7 — çdo dalje shoqërohet me shënimin për profesionistin."""
    for document in documents:
        assert DISCLAIMER_SQ in build(document.context)


def test_critical_banner_comes_before_any_explanation():
    """SP4 — njoftimi paraprin tekstin shpjegues, nuk fshihet brenda tij."""
    document = next(
        d for d in (_document(f"crit{i}") for i in range(40)) if d.context.critical_findings()
    )
    text = build(document.context)
    assert text.startswith(CRITICAL_BANNER_SQ)


def test_uninterpretable_values_are_not_interpreted():
    """SP5 — njoftimi zëvendëson interpretimin."""
    document = next(
        d
        for d in (_document(f"unint{i}") for i in range(40))
        if any(f.ref_source.value == "none" for f in d.context.findings)
    )
    text = build(document.context)
    assert "nuk u gjet interval referent" in text


def test_physician_assertions_are_quoted_verbatim(documents):
    """R5, R6 dhe R8 plotësohen njëherësh sepse teksti nuk preket fare."""
    for document in documents:
        text = build(document.context)
        for assertion in document.context.assertions:
            assert f"{ATTRIBUTION_PREFIX_SQ} {assertion.text_span}." in text


def test_quoted_sentences_are_recognisable_as_quotes(documents):
    document = documents[0]
    quoted = [s.text for s in sentences(build(document.context)) if is_attributed(s.text)]
    assert len(quoted) == len(document.context.assertions)


def test_template_uses_no_number_outside_the_context(documents):
    for document in documents:
        text = build(document.context)
        allowed = document.context.all_grounded_numbers()
        for value, raw in numbers_in(text, document.context):
            assert value in allowed, raw


# --------------------------------------------------------------------
# Rregullat, një nga një
# --------------------------------------------------------------------


@pytest.fixture(scope="module")
def clean(documents):
    document = documents[0]
    return document.context, build(document.context)


def _types(context, text) -> set[ViolationType]:
    return {v.type for v in verify(context, text).violations}


def test_r1_catches_an_invented_number(clean):
    context, text = clean
    assert ViolationType.UNGROUNDED_NUMBER in _types(context, text + " Vlera ishte 99999.")


def test_r2_catches_an_unmeasured_analyte(clean):
    context, text = clean
    intruder = next(
        name
        for name in ("Homocisteinë në serum", "Prokalcitoninë")
        if name not in text
    )
    assert ViolationType.UNGROUNDED_ANALYTE in _types(context, f"{text} {intruder} është e lartë.")


def test_r4_catches_a_missing_critical_value():
    """Mungesa nuk shihet duke lexuar fjalitë që mbetën."""
    document = next(
        d for d in (_document(f"miss{i}") for i in range(40)) if d.context.critical_findings()
    )
    assert ViolationType.MISSING_CRITICAL in _types(document.context, DISCLAIMER_SQ)


def test_r8_catches_a_deleted_recommendation():
    document = next(
        d
        for d in (_document(f"rec{i}") for i in range(20))
        if any(a.kind.value == "recommendation" for a in d.context.assertions)
    )
    text = build(document.context)
    recommendation = next(
        a for a in document.context.assertions if a.kind.value == "recommendation"
    )
    stripped = text.replace(f"{ATTRIBUTION_PREFIX_SQ} {recommendation.text_span}.", "")
    assert ViolationType.OMITTED_RECOMMENDATION in _types(document.context, stripped)


def test_r5_catches_a_flipped_negation():
    document = next(
        d
        for d in (_document(f"neg{i}") for i in range(40))
        if any(a.polarity.value == "negated" for a in d.context.assertions)
    )
    text = build(document.context)
    negated = next(a for a in document.context.assertions if a.polarity.value == "negated")
    flipped = text.replace(
        f"{ATTRIBUTION_PREFIX_SQ} {negated.text_span}.",
        f"{ATTRIBUTION_PREFIX_SQ} {negated.text_span.replace('nuk ', '')}.",
    )
    assert ViolationType.POLARITY_FLIP in _types(document.context, flipped)


def test_prohibited_claims_are_refused(clean):
    """SP1-SP3 — as diagnozë, as trajtim, as prognozë."""
    context, text = clean
    for claim in (
        "Ju vuani nga diabeti.",
        "Merrni dy tableta në ditë.",
        "Gjendja juaj do të përmirësohet brenda javës.",
    ):
        assert ViolationType.PROHIBITED_CLAIM in _types(context, f"{text} {claim}"), claim


def test_rules_carry_no_confidence(clean):
    """Rregullat janë deterministe: ato ose e shohin shkeljen ose jo."""
    context, text = clean
    for violation in verify(context, text + " Vlera ishte 99999.").violations:
        assert violation.confidence is None


def test_catalogue_covers_every_violation_type():
    covered = {rule_id for rule_id, _ in RULES}
    assert covered == {"R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "SP1-3"}


# --------------------------------------------------------------------
# Kurthet e njohura
# --------------------------------------------------------------------


def test_digits_inside_units_are_not_values(clean):
    """`10^9/L` përmban 10 dhe 9; ato nuk janë vlera të përmendura."""
    context, _ = clean
    assert numbers_in("Vlera 286 10^9/L", context) == [
        (__import__("decimal").Decimal("286"), "286")
    ]


def test_decimal_point_does_not_end_a_sentence(clean):
    context, _ = clean
    found = sentences("Vlera është 13.2 g/dL, brenda kufijve. Fjalia tjetër.")
    assert len(found) == 2


def test_quoted_physician_claims_are_not_judged_against_measurements():
    """Një mjek që e ka gabim nuk është gabim i sistemit.

    Citimi gjykohet kundrejt burimit nga R5; krahasimi me matjen do ta
    kthente çdo mospërputhje raport-laborator në shkelje të gjenerimit.
    """
    document = next(
        d
        for d in (_document(f"contra{i}") for i in range(40))
        if any(r.state.value == "contradiction" for r in d.context.cross_refs)
    )
    assert verify(document.context, build(document.context)).passed
