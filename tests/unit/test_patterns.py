"""
Testet e kombinimeve ndërmjet analiteve.

Gjetjet ndërtohen me dorë nga tabela e analiteve, jo nga gjeneruesi:
korpusi prodhon vlera të pavarura për çdo analit, prandaj kombinimet
aty janë të rralla (rreth një në njëzet dokumente) dhe rastet kufitare
— analit i dyfishtë, vlerë pa interval, drejtime të kundërta — nuk
shfaqen dot me vullnet.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from analyte.catalog import analytes_by_code, load_analytes, load_patterns
from analyte.domain.enums import (
    AnalyteStatus,
    AssertionKind,
    Certainty,
    Direction,
    Polarity,
    ReferenceSource,
    ViolationType,
)
from analyte.domain.models import (
    AnalyteFinding,
    GlossaryEntry,
    GroundingContext,
    PatternObservation,
    ReportAssertion,
)
from analyte.domain.policy import ATTRIBUTION_PREFIX_SQ
from analyte.generation.templates import build
from analyte.grounding.branch_a.patterns import detect
from analyte.verification.pipeline import verify

S = AnalyteStatus


def finding(code: str, status: AnalyteStatus) -> AnalyteFinding:
    """Një gjetje e qëndrueshme me statusin e kërkuar."""
    analyte = analytes_by_code()[code]
    if status is S.UNINTERPRETABLE:
        return AnalyteFinding(
            analyte_code=code,
            analyte_name_raw=analyte.name_canonical_sq,
            analyte_name_canonical=analyte.name_canonical_sq,
            value_raw="5",
            value=Decimal("5"),
            unit_canonical=analyte.unit,
            value_canonical=Decimal("5"),
            ref_source=ReferenceSource.NONE,
            status=status,
            page=1,
        )

    low, high = analyte.ref_low_f, analyte.ref_high_f
    width = high - low
    value = {
        S.CRITICAL_LOW: low - width,
        S.LOW: low - width / 10,
        S.NORMAL: (low + high) / 2,
        S.HIGH: high + width / 10,
        S.CRITICAL_HIGH: high + width,
    }[status].quantize(Decimal("0.01"))
    severity = None
    if status.is_abnormal:
        severity = (abs(value - (low if value < low else high)) / width).quantize(Decimal("0.001"))
    return AnalyteFinding(
        analyte_code=code,
        analyte_name_raw=analyte.name_canonical_sq,
        analyte_name_canonical=analyte.name_canonical_sq,
        value_raw=str(value),
        value=value,
        unit_canonical=analyte.unit,
        value_canonical=value,
        ref_low=low,
        ref_high=high,
        ref_source=ReferenceSource.INTERNAL_TABLE,
        status=status,
        severity=severity,
        page=1,
    )


HB, FERRITIN, TSH, FT4, GLUCOSE = "718-7", "2276-4", "3016-3", "3024-7", "2345-7"


def _ids(observed):
    return [o.pattern_id for o in observed]


# --------------------------------------------------------------------
# Zbulimi
# --------------------------------------------------------------------


def test_combination_is_observed_when_every_condition_holds():
    assert _ids(detect((finding(HB, S.LOW), finding(FERRITIN, S.LOW)))) == ["P01"]


def test_a_critical_value_counts_as_its_direction():
    """Rregulli që hesht te vlerat më të rënda do të ishte i pakuptimtë."""
    assert "P01" in _ids(detect((finding(HB, S.CRITICAL_LOW), finding(FERRITIN, S.LOW))))


def test_half_a_combination_is_not_a_combination():
    assert _ids(detect((finding(HB, S.LOW), finding(FERRITIN, S.NORMAL)))) == []


def test_the_wrong_direction_does_not_match():
    assert _ids(detect((finding(HB, S.HIGH), finding(FERRITIN, S.LOW)))) == []


def test_a_value_without_interval_never_takes_part():
    """SP5 — një rregull kombinimi nuk e interpreton dot tërthorazi."""
    observed = detect((finding(HB, S.LOW), finding(FERRITIN, S.UNINTERPRETABLE)))
    assert observed == ()


def test_a_repeated_analyte_is_not_resolved_by_guessing():
    findings = (finding(HB, S.LOW), finding(HB, S.NORMAL), finding(FERRITIN, S.LOW))
    assert "P01" not in _ids(detect(findings))


def test_opposite_directions_in_one_combination():
    assert _ids(detect((finding(TSH, S.HIGH), finding(FT4, S.LOW)))) == ["P08"]
    assert _ids(detect((finding(TSH, S.LOW), finding(FT4, S.HIGH)))) == ["P09"]


def test_observation_points_at_the_findings_that_formed_it():
    hb, ferritin = finding(HB, S.LOW), finding(FERRITIN, S.LOW)
    (observation,) = detect((finding(GLUCOSE, S.HIGH), hb, ferritin))
    assert set(observation.finding_ids) == {hb.id, ferritin.id}


# --------------------------------------------------------------------
# Tabela
# --------------------------------------------------------------------


def test_every_pattern_is_well_formed():
    """Çdo kusht i referohet një analiti që sistemi mund ta interpretojë."""
    interpretable = {a.loinc_code for a in load_analytes()}
    directions = {Direction.INCREASED.value, Direction.DECREASED.value}
    patterns = load_patterns()

    assert len({p.pattern_id for p in patterns}) == len(patterns)
    for pattern in patterns:
        assert len(pattern.conditions) >= 2, pattern.pattern_id
        for code, direction in pattern.conditions:
            assert code in interpretable, (pattern.pattern_id, code)
            assert direction in directions, (pattern.pattern_id, direction)
        assert pattern.source_ref.strip(), pattern.pattern_id


def test_every_pattern_can_fire():
    """Një rresht që nuk ndizet kurrë është gabim shtypi, jo rregull."""
    to_status = {"increased": S.HIGH, "decreased": S.LOW}
    for pattern in load_patterns():
        findings = tuple(finding(code, to_status[d]) for code, d in pattern.conditions)
        assert pattern.pattern_id in _ids(detect(findings))


# --------------------------------------------------------------------
# Konteksti dhe dalja
# --------------------------------------------------------------------


def test_context_refuses_an_observation_about_a_missing_finding():
    with pytest.raises(ValueError, match="P01"):
        GroundingContext(
            document_id=uuid4(),
            findings=(finding(HB, S.LOW),),
            patterns=(
                PatternObservation(
                    pattern_id="P01", finding_ids=(uuid4(), uuid4()), source_ref="x"
                ),
            ),
        )


@pytest.mark.parametrize(
    "statuses",
    [
        {HB: S.LOW, FERRITIN: S.LOW},
        {TSH: S.HIGH, FT4: S.LOW},
        {HB: S.CRITICAL_LOW, FERRITIN: S.LOW, GLUCOSE: S.NORMAL},
    ],
)
def test_template_states_the_combination_and_passes_every_rule(statuses):
    """Fjalia nuk emërton gjendje (SP1, R7) dhe nuk përzien drejtime (R3)."""
    findings = tuple(finding(code, status) for code, status in statuses.items())
    context = GroundingContext(document_id=uuid4(), findings=findings, patterns=detect(findings))
    text = build(context)

    assert "njëkohësisht jashtë intervalit referent" in text
    result = verify(context, text)
    assert result.passed, [(v.type.value, v.evidence) for v in result.violations]


# --------------------------------------------------------------------
# Rregullat e ndrequra në r1.2
# --------------------------------------------------------------------


def test_r6_judges_the_verbatim_quote_not_a_neighbour():
    """Dy citime ndajnë "hepatik"; rezerva gjykohet te citimi i vet."""
    def said(span, certainty):
        return ReportAssertion(
            text_span=span,
            direction=Direction.UNSPECIFIED,
            polarity=Polarity.AFFIRMED,
            certainty=certainty,
            kind=AssertionKind.TERM_MENTION,
            char_start=0,
            char_end=len(span),
        )

    context = GroundingContext(
        document_id=uuid4(),
        assertions=(
            said("Funksioni hepatik është kontrolluar plotësisht", Certainty.CONFIRMED),
            said("Ekografia sugjeron steatozë hepatike", Certainty.HEDGED),
        ),
    )
    text = " ".join(f"{ATTRIBUTION_PREFIX_SQ} {a.text_span}." for a in context.assertions)
    assert verify(context, text).by_type(ViolationType.HEDGE_REMOVED) == ()


def test_r2_accepts_an_analyte_named_inside_a_glossary_explanation():
    """"Qelizat e kuqe" te shpjegimi i hemoglobinës nuk pretendon matje."""
    entry = GlossaryEntry(
        term="hemoglobinë",
        explanation_sq="proteina që bart oksigjenin në qelizat e kuqe",
        source_ref="x",
    )
    context = GroundingContext(document_id=uuid4(), glossary=(entry,))
    text = f"Hemoglobinë do të thotë {entry.explanation_sq}."
    assert verify(context, text).by_type(ViolationType.UNGROUNDED_ANALYTE) == ()


def test_r2_still_refuses_that_analyte_outside_the_explanation():
    context = GroundingContext(document_id=uuid4())
    text = "Qelizat e kuqe tuaja janë në rregull."
    assert verify(context, text).by_type(ViolationType.UNGROUNDED_ANALYTE) != ()
