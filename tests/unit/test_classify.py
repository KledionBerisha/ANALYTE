"""
Testet e klasifikimit determinist.

"""

from decimal import Decimal

from analyte.domain.enums import AnalyteStatus
from analyte.grounding.branch_a.classify import classify

LOW = Decimal(70)
HIGH = Decimal(99)
CRIT_LOW = Decimal(45)
CRIT_HIGH = Decimal(400)


def _classify(value: str):
    return classify(Decimal(value), LOW, HIGH, CRIT_LOW, CRIT_HIGH)


def test_value_inside_interval_is_normal():
    result = _classify("85")
    assert result.status is AnalyteStatus.NORMAL
    assert result.severity is None


def test_interval_bounds_are_inclusive():
    """Vlera pikërisht mbi kufi është ende normale: intervali referent
    shtypet si i mbyllur dhe pacienti e lexon ashtu."""
    assert _classify("70").status is AnalyteStatus.NORMAL
    assert _classify("99").status is AnalyteStatus.NORMAL


def test_above_and_below_interval():
    assert _classify("128").status is AnalyteStatus.HIGH
    assert _classify("60").status is AnalyteStatus.LOW


def test_critical_thresholds_are_inclusive():
    assert _classify("400").status is AnalyteStatus.CRITICAL_HIGH
    assert _classify("45").status is AnalyteStatus.CRITICAL_LOW
    assert _classify("401").status is AnalyteStatus.CRITICAL_HIGH
    assert _classify("46").status is AnalyteStatus.LOW


def test_severity_is_distance_in_interval_widths():
    """(128 - 99) / (99 - 70) = 1.0 — i njëjti përkufizim si në fixture-in
    referues të domenit."""
    assert _classify("128").severity == Decimal("1.0000")
    assert _classify("41.5").severity == Decimal("0.9828")


def test_missing_interval_is_uninterpretable():
    result = classify(Decimal(212), None, None)
    assert result.status is AnalyteStatus.UNINTERPRETABLE
    assert result.severity is None


def test_one_sided_interval_uses_the_crossed_bound_as_scale():
    """Me interval "< 200" nuk ka gjerësi; ashpërsia bëhet devijim
    relativ ndaj kufirit të kaluar."""
    result = classify(Decimal(250), None, Decimal(200))
    assert result.status is AnalyteStatus.HIGH
    assert result.severity == Decimal("0.2500")


def test_without_critical_threshold_extreme_values_stay_high():
    """Aty ku laboratori nuk përcakton prag paniku, ne nuk shpikim një të tillë."""
    result = classify(Decimal(9999), LOW, HIGH)
    assert result.status is AnalyteStatus.HIGH
