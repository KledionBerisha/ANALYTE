"""
Zgjidhja e intervalit referent.

"""

from __future__ import annotations

import re
from decimal import Decimal

from analyte.catalog import Analyte, Sex, conversion_for
from analyte.domain.enums import ReferenceSource

from .normalize import normalize_unit, parse_number

INTERVAL = re.compile(r"^(?P<low>[+-]?\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<high>[+-]?\d+(?:[.,]\d+)?)$")
"""Interval dyanësh: "70 - 99". Vijat e ndryshme të ndarjes janë të gjitha
vizë; shtypshkrimi ndryshon nga laboratori në laborator."""

ONE_SIDED = re.compile(r"^(?P<operator>[<>≤≥])\s*(?P<bound>[+-]?\d+(?:[.,]\d+)?)$")
"""Interval njëanësh: "< 200". I zakonshëm te lipidet dhe te shënuesit."""


class Resolution:
    """Rezultati i zgjidhjes: kufijtë dhe nga erdhën."""

    __slots__ = ("high", "low", "source")

    def __init__(self, low: Decimal | None, high: Decimal | None, source: ReferenceSource) -> None:
        self.low, self.high, self.source = low, high, source

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Resolution) and (
            (self.low, self.high, self.source) == (other.low, other.high, other.source)
        )

    def __repr__(self) -> str:  # pragma: no cover - vetëm për diagnostikim
        return f"Resolution({self.low}, {self.high}, {self.source.value})"

    @property
    def has_bounds(self) -> bool:
        return self.low is not None or self.high is not None


NONE_FOUND = Resolution(None, None, ReferenceSource.NONE)


def parse_printed(text: str) -> tuple[Decimal | None, Decimal | None] | None:
    """Lexon intervalin ashtu si është shtypur, pa e kthyer në njësi."""
    candidate = text.strip()

    match = INTERVAL.match(candidate)
    if match:
        low = parse_number(match.group("low"))
        high = parse_number(match.group("high"))
        if low is None or high is None or low >= high:
            return None
        return low, high

    match = ONE_SIDED.match(candidate)
    if match:
        bound = parse_number(match.group("bound"))
        if bound is None:
            return None
        return (None, bound) if match.group("operator") in "<≤" else (bound, None)

    return None


def resolve(
    analyte: Analyte,
    printed: str | None,
    printed_unit: str,
    sex: Sex | None,
) -> Resolution:
    """Zgjedh intervalin për një gjetje, sipas përparësisë së burimeve."""
    if printed:
        bounds = parse_printed(printed)
        if bounds is not None:
            low, high = _to_canonical_bounds(analyte, bounds, printed_unit)
            return Resolution(low, high, ReferenceSource.DOCUMENT)

    if analyte.has_reference and sex is not None:
        low, high = analyte.reference_for(sex)
        return Resolution(low, high, ReferenceSource.INTERNAL_TABLE)

    # Gjinia e panjohur te një analit që varet prej saj nuk zgjidhet me
    # hamendje: do të thoshte zgjedhje e intervalit me short.
    return NONE_FOUND


def _to_canonical_bounds(
    analyte: Analyte,
    bounds: tuple[Decimal | None, Decimal | None],
    printed_unit: str,
) -> tuple[Decimal | None, Decimal | None]:
    """Kufijtë e shtypur janë në njësinë e shtypur, jo në atë kanonike.

    Një interval "62 - 115" umol/L dhe një vlerë 152 umol/L janë të
    krahasueshme mes tyre, por jo me kufijtë e tabelës në mg/dL. Kthimi
    duhet bërë në të dyja anët ose në asnjërën.
    """
    unit = normalize_unit(printed_unit)
    conversion = conversion_for(analyte)
    if conversion is None or unit != conversion.unit_from:
        return bounds

    low, high = bounds
    return (
        analyte.quantize(conversion.to_canonical(low)) if low is not None else None,
        analyte.quantize(conversion.to_canonical(high)) if high is not None else None,
    )
