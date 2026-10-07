"""
PK2 — saktësia e klasifikimit të statusit.

"""

from __future__ import annotations

from typing import Any

from analyte.domain.enums import AnalyteStatus, ReferenceSource
from analyte.domain.models import GroundingContext

from .base import ConfusionMatrix, _round


def measure(pairs: list[tuple[GroundingContext, GroundingContext]]) -> dict[str, Any]:
    overall = ConfusionMatrix()
    by_source: dict[str, ConfusionMatrix] = {}
    unmatched = 0

    for truth, predicted in pairs:
        predicted_by_code = {f.analyte_code: f for f in predicted.findings}
        for finding in truth.findings:
            match = predicted_by_code.get(finding.analyte_code)
            if match is None:
                unmatched += 1
                continue
            overall.add(finding.status.value, match.status.value)
            source = by_source.setdefault(finding.ref_source.value, ConfusionMatrix())
            source.add(finding.status.value, match.status.value)

    return {
        "overall": overall.to_json(),
        "by_reference_source": {
            source: matrix.to_json() for source, matrix in sorted(by_source.items())
        },
        "reference_source_share": _source_share(pairs),
        "unmatched_findings": unmatched,
        "uninterpretable_recall": _round(_uninterpretable_recall(overall)),
    }


def _source_share(
    pairs: list[tuple[GroundingContext, GroundingContext]],
) -> dict[str, float | None]:
    """Nga erdhi intervali, sipas së vërtetës bazë.

    Kjo nuk është metrikë suksesi por përshkrim i korpusit; pa të,
    saktësia e ndarë sipas burimit nuk lexohet dot.
    """
    counts = dict.fromkeys((s.value for s in ReferenceSource), 0)
    total = 0
    for truth, _ in pairs:
        for finding in truth.findings:
            counts[finding.ref_source.value] += 1
            total += 1
    return {
        source: _round(count / total) if total else None for source, count in sorted(counts.items())
    }


def _uninterpretable_recall(matrix: ConfusionMatrix) -> float | None:
    """Sa nga vlerat e painterpretueshme u njohën si të tilla.

    Kjo është SP5 e shprehur si numër. Një sistem që hamendëson një status
    aty ku nuk ka interval referent shkel politikën e sigurisë, dhe
    saktësia e përgjithshme do ta fshihte këtë sepse rastet janë të pakta.
    """
    per_class = matrix.per_class()
    counts = per_class.get(AnalyteStatus.UNINTERPRETABLE.value)
    return counts.recall if counts else None
