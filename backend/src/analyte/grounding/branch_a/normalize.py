"""
Normalizimi i numrave dhe i njësive.

"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from analyte.catalog import Analyte, conversion_for

NUMBER = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")
"""Një numër i vetëm, me presje ose me pikë. Asgjë tjetër nuk pranohet."""


def parse_number(text: str) -> Decimal | None:
    """Kthen numrin e shtypur në Decimal, ose None nëse nuk është numër."""
    candidate = text.strip().replace(" ", " ").replace(" ", "")
    if not NUMBER.match(candidate):
        return None
    try:
        return Decimal(candidate.replace(",", "."))
    except InvalidOperation:
        return None


def normalize_unit(text: str | None) -> str:
    """Pastron njësinë e shtypur pa e kthyer.

    Hiqen hapësirat dhe rregullohen variantet e zakonshme të shkrimit.
    Nuk bëhet asnjë njësim më i thellë: "mg/dl" dhe "mg/dL" janë e njëjta
    njësi, por "mg/dL" dhe "mmol/L" nuk janë, dhe ngatërrimi i tyre do të
    ishte katastrofë e heshtur.
    """
    if not text:
        return ""
    cleaned = text.strip().replace(" ", "").replace("µ", "u").replace("μ", "u")
    return _CANONICAL_SPELLING.get(cleaned.casefold(), cleaned)


_CANONICAL_SPELLING: dict[str, str] = {
    "mg/dl": "mg/dL",
    "g/dl": "g/dL",
    "g/l": "g/L",
    "mmol/l": "mmol/L",
    "umol/l": "umol/L",
    "ug/dl": "ug/dL",
    "ng/ml": "ng/mL",
    "pg/ml": "pg/mL",
    "u/l": "U/L",
    "miu/l": "mIU/L",
    "10^9/l": "10^9/L",
    "10^12/l": "10^12/L",
    "fl": "fL",
    "pg": "pg",
    "%": "%",
}


def to_canonical(analyte: Analyte, value: Decimal, unit: str) -> tuple[Decimal, str] | None:
    """Kthen vlerën në njësinë kanonike të analitit.

    Kthen None kur njësia e shtypur nuk është as ajo kanonike dhe as ajo
    alternative e njohur. Kjo nuk është dështim i vogël: një vlerë në
    njësi të panjohur nuk mund të krahasohet me asnjë interval, prandaj
    thirrësi duhet ta shënojë gjetjen të painterpretueshme (SP5) në vend
    që ta kalojë ashtu siç është.
    """
    unit = normalize_unit(unit)
    if unit == analyte.unit or not unit:
        return value, analyte.unit

    conversion = conversion_for(analyte)
    if conversion is not None and unit == conversion.unit_from:
        converted = analyte.quantize(conversion.to_canonical(value))
        return converted, analyte.unit

    return None


def split_value_and_unit(text: str) -> tuple[Decimal, str] | None:
    """Ndan "13,4 g/dL" në numër dhe njësi.

    Formati kompakt i shtyp të dyja në një qelizë, ndërsa ai tabelor i
    ndan në kolona; nxjerrësi duhet t'i durojë të dyja pa e ditur
    paraprakisht se cili format është.
    """
    stripped = text.strip()
    if not stripped:
        return None

    parts = stripped.split(None, 1)
    number = parse_number(parts[0])
    if number is None:
        return None
    return number, normalize_unit(parts[1]) if len(parts) > 1 else ""
