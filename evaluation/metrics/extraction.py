"""
PK1 — saktësia e nxjerrjes së vlerave laboratorike.

Matet për fushë: analiti, vlera, njësia dhe intervali referent. Një fushë
numërohet e saktë vetëm me përputhje të plotë pas normalizimit; nuk ka
pikë të pjesshme. Kjo është zgjedhje e ashpër dhe e qëllimshme — një
vlerë e nxjerrë "pothuajse saktë" është vlerë e gabuar në një raport
mjekësor.

**Si përputhen rreshtat.** Nxjerrja nuk i kthen gjetjet me identifikues;
ato duhen çiftuar me të vërtetën bazë. Çiftimi bëhet me kodin LOINC:

  - kod i parashikuar që gjendet te e vërteta  → çift për shqyrtim fushash
  - kod i parashikuar që nuk gjendet           → fals pozitiv (analit i shpikur)
  - kod i vërtetë që nuk u parashikua          → fals negativ, dhe me të
                                                 humbin edhe të gjitha fushat e tij

Pasoja e fundit ka rëndësi: një rresht i humbur nuk është neutral për
fushat e tij. Po të mos numërohej ashtu, një sistem që nxjerr vetëm
rreshtat e lehtë do të dukej i përsosur.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from analyte.domain.models import AnalyteFinding, GroundingContext

from .base import PRF, macro_f1, micro_average

FIELDS: tuple[str, ...] = ("analyte", "value", "unit", "interval")


def measure(pairs: list[tuple[GroundingContext, GroundingContext]]) -> dict[str, Any]:
    """Mat nxjerrjen mbi çiftet (e vërteta, e parashikuara)."""
    per_field: dict[str, PRF] = {field: PRF(0, 0, 0) for field in FIELDS}

    for truth, predicted in pairs:
        for field, counts in _document_counts(truth, predicted).items():
            per_field[field] = per_field[field] + counts

    micro = micro_average(per_field)
    return {
        "per_field": {field: counts.to_json() for field, counts in per_field.items()},
        "micro": micro.to_json(),
        "macro_f1": macro_f1(per_field),
        "documents": len(pairs),
    }


def _document_counts(
    truth: GroundingContext, predicted: GroundingContext
) -> dict[str, PRF]:
    truth_by_code = _by_code(truth)
    predicted_by_code = _by_code(predicted)

    matched = truth_by_code.keys() & predicted_by_code.keys()
    missed = truth_by_code.keys() - predicted_by_code.keys()
    invented = predicted_by_code.keys() - truth_by_code.keys()

    counts = {
        "analyte": PRF(len(matched), len(invented), len(missed)),
    }

    for field in ("value", "unit", "interval"):
        true_positive = sum(
            1
            for code in matched
            if _field_matches(field, truth_by_code[code], predicted_by_code[code])
        )
        wrong = len(matched) - true_positive
        # Një fushë e nxjerrë gabim është njëkohësisht pohim i rremë dhe
        # mungesë e të vërtetës, prandaj numërohet në të dyja anët.
        counts[field] = PRF(true_positive, wrong + len(invented), wrong + len(missed))

    return counts


def _by_code(context: GroundingContext) -> dict[str, AnalyteFinding]:
    """Gjetjet sipas kodit.

    Një analit shfaqet një herë për dokument te korpusi ynë. Nëse nxjerrja
    kthen dublikata, mbahet e para dhe pjesa tjetër humbet — çka e ul
    saktësinë e saj, ashtu si duhet.
    """
    out: dict[str, AnalyteFinding] = {}
    for finding in context.findings:
        out.setdefault(finding.analyte_code, finding)
    return out


def _field_matches(field: str, truth: AnalyteFinding, predicted: AnalyteFinding) -> bool:
    if field == "value":
        # Krahasohet vlera e normalizuar: nxjerrja mund ta ketë lexuar
        # saktë vlerën e shtypur në njësi tjetër, dhe ajo është sukses.
        return _same_number(truth.value_canonical, predicted.value_canonical)
    if field == "unit":
        return truth.unit_canonical == predicted.unit_canonical
    if field == "interval":
        return _same_number(truth.ref_low, predicted.ref_low) and _same_number(
            truth.ref_high, predicted.ref_high
        )
    raise ValueError(f"fushë e panjohur: {field}")


def _same_number(left: Decimal | None, right: Decimal | None) -> bool:
    """Barazi numerike, jo barazi vargjesh.

    `Decimal("5.0") == Decimal("5.00")` është e vërtetë, ndërsa vargjet e
    tyre ndryshojnë. Numri i presjeve të shtypura nuk është pjesë e
    vlerës.
    """
    if left is None or right is None:
        return left is None and right is None
    return left == right
