"""
Klasifikimi determinist i një vlere kundrejt intervalit referent.

Ky është i vetmi vend ku përkufizohet se çfarë do të thotë "e lartë",
"kritike" ose "e painterpretueshme". Edhe gjeneruesi i të dhënave
sintetike e përdor këtë funksion për të prodhuar etiketat e së vërtetës
bazë. Kjo nuk e bën matjen e PK2 tautologjike: klasifikimi është i
dhënë me rregull, prandaj PK2 mat nëse u nxorën vlera dhe intervali i
duhur — jo nëse rregulli u mësua. Nëse do të kishim dy zbatime të
rregullit, ndryshimi mes tyre do të shfaqej si gabim i sistemit dhe do
ta bënte matjen të pakuptimtë.

Moduli është i pastër: pa I/O, pa gjendje, pa varësi jashtë `domain/`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple

from analyte.domain.enums import AnalyteStatus

SEVERITY_PRECISION = Decimal("0.0001")
"""Rrumbullakimi i ashpërsisë. Pa të, pjesëtimi me Decimal jep 28 shifra
dhe dy ekzekutime të njëjta japin vargje JSON të ndryshme."""


class Classification(NamedTuple):
    """Rezultati i klasifikimit: statusi dhe largësia relative."""

    status: AnalyteStatus
    severity: Decimal | None


def classify(
    value: Decimal,
    ref_low: Decimal | None,
    ref_high: Decimal | None,
    critical_low: Decimal | None = None,
    critical_high: Decimal | None = None,
) -> Classification:
    """Klasifikon një vlerë të normalizuar kundrejt intervalit të saj.

    SP5: pa asnjë kufi nuk ka interpretim. Kthehet UNINTERPRETABLE dhe
    severity=None, çka është pikërisht ajo që `AnalyteFinding` kërkon.

    Kufijtë kritikë janë fakultativë. Aty ku laboratori nuk përcakton
    prag panik, një vlerë e jashtëzakonshme mbetet HIGH ose LOW — nuk
    shpikim prag.
    """
    if ref_low is None and ref_high is None:
        return Classification(AnalyteStatus.UNINTERPRETABLE, None)

    if ref_low is not None and value < ref_low:
        critical = critical_low is not None and value <= critical_low
        status = AnalyteStatus.CRITICAL_LOW if critical else AnalyteStatus.LOW
        return Classification(status, _severity(ref_low - value, ref_low, ref_high))

    if ref_high is not None and value > ref_high:
        critical = critical_high is not None and value >= critical_high
        status = AnalyteStatus.CRITICAL_HIGH if critical else AnalyteStatus.HIGH
        return Classification(status, _severity(value - ref_high, ref_low, ref_high))

    return Classification(AnalyteStatus.NORMAL, None)


def _severity(
    distance: Decimal, ref_low: Decimal | None, ref_high: Decimal | None
) -> Decimal:
    """Largësia nga kufiri, e shprehur në gjerësi intervali.

    Me interval dyanësh gjerësia është `ref_high - ref_low`. Me interval
    njëanësh — i zakonshëm në raporte reale, p.sh. "< 200" — ajo gjerësi
    nuk ekziston; atëherë shkalla është vetë kufiri i kaluar, pra
    ashpërsia bëhet devijim relativ. Të dyja rastet japin numër pa njësi
    dhe të krahasueshëm brenda të njëjtit analit; krahasimi mes analitesh
    me lloje të ndryshme intervali nuk është i vlefshëm dhe nuk përdoret.
    """
    if ref_low is not None and ref_high is not None:
        scale = ref_high - ref_low
    else:
        bound = ref_high if ref_high is not None else ref_low
        assert bound is not None  # njëri prej tyre ekziston gjithnjë këtu
        scale = abs(bound)

    if scale == 0:
        scale = Decimal(1)

    return (distance / scale).quantize(SEVERITY_PRECISION)
