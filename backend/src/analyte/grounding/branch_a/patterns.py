"""
Zbulimi i kombinimeve ndërmjet analiteve.

"""

from __future__ import annotations

from collections import Counter

from analyte.catalog import Pattern, load_patterns
from analyte.domain.models import AnalyteFinding, PatternObservation


def detect(
    findings: tuple[AnalyteFinding, ...],
    patterns: tuple[Pattern, ...] | None = None,
) -> tuple[PatternObservation, ...]:
    """Kombinimet e plotësuara nga gjetjet e një dokumenti, në rendin e tabelës."""
    patterns = load_patterns() if patterns is None else patterns
    counts = Counter(f.analyte_code for f in findings)
    by_code = {f.analyte_code: f for f in findings if counts[f.analyte_code] == 1}

    observed: list[PatternObservation] = []
    for pattern in patterns:
        matched = [
            by_code[code]
            for code, direction in pattern.conditions
            if code in by_code and by_code[code].status.direction.value == direction
        ]
        if len(matched) == len(pattern.conditions):
            observed.append(
                PatternObservation(
                    pattern_id=pattern.pattern_id,
                    finding_ids=tuple(f.id for f in matched),
                    source_ref=pattern.source_ref,
                )
            )
    return tuple(observed)
