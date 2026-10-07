"""
Këshillat me burim për gjetjet jashtë intervalit (ADR 0023).

"""

from __future__ import annotations

from collections import Counter

from analyte.catalog import Advice, advice_by_key
from analyte.domain.enums import Direction
from analyte.domain.models import AdviceEntry, AnalyteFinding

ADVISED_DIRECTIONS = (Direction.INCREASED, Direction.DECREASED)


def attach(
    findings: tuple[AnalyteFinding, ...],
    advice: tuple[Advice, ...] | None = None,
) -> tuple[AdviceEntry, ...]:
    """Këshillat e tabelës për gjetjet e një dokumenti, në rendin e gjetjeve."""
    table = advice_by_key() if advice is None else {(a.loinc_code, a.direction): a for a in advice}
    counts = Counter(f.analyte_code for f in findings)

    out: list[AdviceEntry] = []
    for finding in findings:
        direction = finding.status.direction
        if direction not in ADVISED_DIRECTIONS or counts[finding.analyte_code] != 1:
            continue
        row = table.get((finding.analyte_code, direction.value))
        if row is None or not row.is_filled:
            continue
        out.append(
            AdviceEntry(
                finding_id=finding.id,
                analyte_code=finding.analyte_code,
                direction=direction,
                advice_sq=row.advice_sq,
                source_ref=row.source_ref,
            )
        )
    return tuple(out)
