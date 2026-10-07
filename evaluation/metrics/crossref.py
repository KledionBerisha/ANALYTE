"""
PK4 — saktësia e krahasimit raport ↔ laborator.

"""

from __future__ import annotations

from typing import Any

from analyte.domain.enums import CrossReferenceState
from analyte.domain.models import GroundingContext

from .base import ConfusionMatrix, _round

MISSING = "missing"
"""Etiketë e parashikimit kur ai nuk thotë asgjë për një analit."""


def measure(pairs: list[tuple[GroundingContext, GroundingContext]]) -> dict[str, Any]:
    matrix = ConfusionMatrix()
    spurious = 0

    for truth, predicted in pairs:
        truth_states = {ref.analyte_code: ref.state.value for ref in truth.cross_refs}
        predicted_states = {ref.analyte_code: ref.state.value for ref in predicted.cross_refs}

        for code, state in truth_states.items():
            matrix.add(state, predicted_states.get(code, MISSING))

        # Gjendje për analite që e vërteta nuk i njeh fare: nuk kanë rresht
        # në matricë sepse nuk kanë etiketë të vërtetë.
        spurious += len(predicted_states.keys() - truth_states.keys())

    per_class = matrix.per_class()
    return {
        "overall": matrix.to_json(),
        "spurious_cross_references": spurious,
        "recall_by_state": {
            state.value: _round(counts.recall)
            for state, counts in (
                (state, per_class.get(state.value)) for state in CrossReferenceState
            )
            if counts is not None
        },
    }
