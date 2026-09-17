"""
Testet e kontratës së domenit.

Këto teste nuk kontrollojnë sjellje biznesi — ato kontrollojnë që
gjendjet e pamundura janë vërtet të pamundura. Çdo test që dështon këtu
tregon se një shtresë tjetër mund të prodhojë të dhëna të pavlefshme.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from analyte.domain.enums import (
    AnalyteStatus,
    AssertionKind,
    Certainty,
    CrossReferenceState,
    DetectedBy,
    Direction,
    Polarity,
    ProcessingState,
    ReferenceSource,
    ViolationType,
)
from analyte.domain.models import (
    AnalyteFinding,
    CrossReference,
    GroundingContext,
    ReportAssertion,
    Violation,
    VerificationResult,
)
from tests.fixtures.grounding_context import build_reference_context


# --------------------------------------------------------------------
# Fixture-i referues
# --------------------------------------------------------------------


@pytest.fixture
def ctx() -> GroundingContext:
    return build_reference_context()


def test_reference_context_builds(ctx):
    assert len(ctx.findings) == 4
    assert len(ctx.assertions) == 4
    assert len(ctx.cross_refs) == 4
    assert not ctx.is_empty()


def test_reference_context_covers_all_cross_reference_states(ctx):
    """Fixture-i duhet të mbulojë të katër gjendjet, përndryshe PK4
    do të testohej vetëm pjesërisht."""
    states = {r.state for r in ctx.cross_refs}
    assert CrossReferenceState.AGREEMENT in states
    assert CrossReferenceState.MENTIONED_NOT_MEASURED in states
    assert CrossReferenceState.MEASURED_NOT_MENTIONED in states


# --------------------------------------------------------------------
# Serializimi — round-trip
# --------------------------------------------------------------------


def test_context_round_trip_preserves_everything(ctx):
    """Konteksti do të ruhet dhe do të lexohet nga baza e të dhënave dhe
    nga skedarët e eksperimenteve. Round-trip-i duhet të jetë i plotë."""
    payload = ctx.model_dump_json()
    restored = GroundingContext.model_validate_json(payload)
    assert restored == ctx


def test_decimal_precision_survives_round_trip():
    """Decimal dhe jo float: 13.4 si float humb saktësinë dhe rregulli R1
    krahason numra për barazi të saktë."""
    ctx = build_reference_context()
    hgb = next(f for f in ctx.findings if f.analyte_code == "718-7")
    assert hgb.value == Decimal("13.4")
    restored = GroundingContext.model_validate_json(ctx.model_dump_json())
    rest_hgb = next(f for f in restored.findings if f.analyte_code == "718-7")
    assert rest_hgb.value == Decimal("13.4")


def test_models_are_immutable(ctx):
    with pytest.raises(ValidationError):
        ctx.findings[0].value = Decimal("999")  # type: ignore[misc]


def test_unknown_field_is_rejected():
    """extra='forbid': një fushë e shkruar gabim duhet të dështojë menjëherë
    dhe jo të injorohet në heshtje."""
    with pytest.raises(ValidationError):
        ReportAssertion(
            text_span="x",
            direction=Direction.NORMAL,
            polarity=Polarity.AFFIRMED,
            certainty=Certainty.CONFIRMED,
            kind=AssertionKind.FINDING,
            char_start=0,
            char_end=1,
            typo_field="oops",  # type: ignore[call-arg]
        )


# --------------------------------------------------------------------
# SP5 — pa interval referent nuk ka interpretim
# --------------------------------------------------------------------


def _finding(**overrides):
    base = dict(
        analyte_code="2345-7",
        analyte_name_raw="Glukoza",
        analyte_name_canonical="Glukozë në serum",
        value_raw="128",
        value=Decimal("128"),
        unit_raw="mg/dL",
        unit_canonical="mg/dL",
        value_canonical=Decimal("128"),
        ref_low=Decimal("70"),
        ref_high=Decimal("99"),
        ref_source=ReferenceSource.DOCUMENT,
        status=AnalyteStatus.HIGH,
        severity=Decimal("1.0"),
        page=1,
    )
    base.update(overrides)
    return AnalyteFinding(**base)


def test_missing_interval_must_be_uninterpretable():
    with pytest.raises(ValidationError, match="UNINTERPRETABLE"):
        _finding(
            ref_low=None,
            ref_high=None,
            ref_source=ReferenceSource.NONE,
            status=AnalyteStatus.HIGH,
            severity=Decimal("1.0"),
        )


def test_uninterpretable_with_interval_is_rejected():
    with pytest.raises(ValidationError):
        _finding(status=AnalyteStatus.UNINTERPRETABLE, severity=None)


def test_reference_source_none_with_bounds_is_rejected():
    with pytest.raises(ValidationError, match="burimi i vërtetë"):
        _finding(ref_source=ReferenceSource.NONE)


def test_inverted_interval_is_rejected():
    with pytest.raises(ValidationError, match="ref_low"):
        _finding(ref_low=Decimal("99"), ref_high=Decimal("70"))


def test_severity_required_for_abnormal_status():
    with pytest.raises(ValidationError, match="severity"):
        _finding(status=AnalyteStatus.HIGH, severity=None)


def test_severity_forbidden_for_normal_status():
    with pytest.raises(ValidationError, match="severity"):
        _finding(
            value=Decimal("85"),
            value_canonical=Decimal("85"),
            status=AnalyteStatus.NORMAL,
            severity=Decimal("0.2"),
        )


# --------------------------------------------------------------------
# Statuset dhe drejtimi (R3)
# --------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        (AnalyteStatus.CRITICAL_LOW, Direction.DECREASED),
        (AnalyteStatus.LOW, Direction.DECREASED),
        (AnalyteStatus.NORMAL, Direction.NORMAL),
        (AnalyteStatus.HIGH, Direction.INCREASED),
        (AnalyteStatus.CRITICAL_HIGH, Direction.INCREASED),
        (AnalyteStatus.UNINTERPRETABLE, Direction.UNSPECIFIED),
    ],
)
def test_status_maps_to_direction(status, expected):
    assert status.direction is expected


def test_critical_statuses_are_also_abnormal():
    for s in (AnalyteStatus.CRITICAL_LOW, AnalyteStatus.CRITICAL_HIGH):
        assert s.is_critical and s.is_abnormal


def test_uninterpretable_is_not_abnormal():
    """E painterpretueshme nuk do të thotë jonormale — mos e trajto si të tillë."""
    assert not AnalyteStatus.UNINTERPRETABLE.is_abnormal
    assert not AnalyteStatus.UNINTERPRETABLE.is_critical


# --------------------------------------------------------------------
# Ndihmësat e verifikimit
# --------------------------------------------------------------------


def test_grounded_numbers_include_value_and_bounds(ctx):
    glu = next(f for f in ctx.findings if f.analyte_code == "2345-7")
    nums = glu.grounded_numbers()
    assert Decimal("128") in nums
    assert Decimal("70") in nums and Decimal("99") in nums


def test_all_grounded_numbers_excludes_absent_values(ctx):
    """Numri që nuk gjendet askund në kontekst duhet të konsiderohet i
    pambështetur — kjo është baza e rregullit R1."""
    nums = ctx.all_grounded_numbers()
    assert Decimal("6.9") in nums          # kaliumi
    assert Decimal("250") not in nums      # i shpikur


def test_critical_findings_are_isolated(ctx):
    crit = ctx.critical_findings()
    assert len(crit) == 1
    assert crit[0].analyte_code == "2823-3"


def test_known_analyte_codes(ctx):
    codes = ctx.known_analyte_codes()
    assert "2345-7" in codes
    assert "2093-3" not in codes  # kolesteroli, i pamatur


def test_status_of_unknown_analyte_is_none(ctx):
    assert ctx.status_of("2093-3") is None
    assert ctx.status_of("2823-3") is AnalyteStatus.CRITICAL_HIGH


def test_empty_context_is_detected():
    empty = GroundingContext(document_id=uuid4())
    assert empty.is_empty()


# --------------------------------------------------------------------
# Integriteti i kontekstit
# --------------------------------------------------------------------


def test_cross_ref_to_unknown_finding_is_rejected():
    with pytest.raises(ValidationError, match="gjetjes së panjohur"):
        GroundingContext(
            document_id=uuid4(),
            cross_refs=(
                CrossReference(
                    analyte_code="2345-7",
                    state=CrossReferenceState.MEASURED_NOT_MENTIONED,
                    finding_id=uuid4(),
                ),
            ),
        )


def test_term_cannot_be_both_explained_and_unexplained(ctx):
    with pytest.raises(ValidationError, match="njëkohësisht"):
        GroundingContext(
            document_id=ctx.document_id,
            glossary=ctx.glossary,
            unexplained_terms=("Transaminaza",),  # përputhet pa dallim shkronjash
        )


def test_agreement_requires_both_sides():
    with pytest.raises(ValidationError, match="assertion_id"):
        CrossReference(
            analyte_code="2345-7",
            state=CrossReferenceState.AGREEMENT,
            finding_id=uuid4(),
        )


def test_mentioned_not_measured_forbids_finding_id():
    with pytest.raises(ValidationError):
        CrossReference(
            analyte_code="2345-7",
            state=CrossReferenceState.MENTIONED_NOT_MEASURED,
            assertion_id=uuid4(),
            finding_id=uuid4(),
        )


def test_assertion_span_must_be_ordered():
    with pytest.raises(ValidationError):
        ReportAssertion(
            text_span="x",
            direction=Direction.NORMAL,
            polarity=Polarity.AFFIRMED,
            certainty=Certainty.CONFIRMED,
            kind=AssertionKind.FINDING,
            char_start=50,
            char_end=10,
        )


# --------------------------------------------------------------------
# Shkeljet dhe rezultati i verifikimit
# --------------------------------------------------------------------


def _violation(**overrides):
    base = dict(
        type=ViolationType.UNGROUNDED_NUMBER,
        detected_by=DetectedBy.RULE,
        sentence="Kolesteroli juaj është 210 mg/dL.",
        evidence="numri 210 nuk gjendet në gjetjet e strukturuara",
    )
    base.update(overrides)
    return Violation(**base)


def test_rule_violation_has_no_confidence():
    with pytest.raises(ValidationError, match="deterministe"):
        _violation(confidence=0.9)


def test_classifier_violation_may_have_confidence():
    v = _violation(
        type=ViolationType.POLARITY_FLIP,
        detected_by=DetectedBy.CLASSIFIER,
        confidence=0.87,
    )
    assert v.confidence == 0.87


def test_verification_passes_only_without_violations():
    clean = VerificationResult(
        explanation_id=uuid4(), rules_version="r1.0", duration_ms=12
    )
    assert clean.passed

    dirty = VerificationResult(
        explanation_id=uuid4(),
        rules_version="r1.0",
        duration_ms=15,
        violations=(_violation(),),
    )
    assert not dirty.passed


def test_violations_split_by_detector():
    """Kjo ndarje është burimi i drejtpërdrejtë i të dhënave për PK6."""
    result = VerificationResult(
        explanation_id=uuid4(),
        rules_version="r1.0",
        classifier_version="xlmr-v1",
        duration_ms=40,
        violations=(
            _violation(),
            _violation(
                type=ViolationType.HEDGE_REMOVED,
                detected_by=DetectedBy.CLASSIFIER,
                confidence=0.71,
            ),
        ),
    )
    assert len(result.by_detector(DetectedBy.RULE)) == 1
    assert len(result.by_detector(DetectedBy.CLASSIFIER)) == 1
    assert len(result.by_type(ViolationType.HEDGE_REMOVED)) == 1


def test_violation_types_map_to_correct_branch():
    assert ViolationType.UNGROUNDED_NUMBER.branch == "A"
    assert ViolationType.POLARITY_FLIP.branch == "B"


# --------------------------------------------------------------------
# Makina e gjendjeve
# --------------------------------------------------------------------


def test_terminal_states():
    assert ProcessingState.DELIVERED.is_terminal
    assert ProcessingState.NO_FINDINGS.is_terminal
    assert not ProcessingState.GENERATING.is_terminal
