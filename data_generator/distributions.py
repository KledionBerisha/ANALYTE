"""
Kampionimi i vlerave me shkallë të kontrolluar jonormaliteti.

Dy kërkesa përcaktojnë zbatimin:

1. Përsëritshmëria (NFR3). Çdo kampionim bëhet mbi numra të plotë hapash
   të rrumbullakimit, jo mbi float. Kështu vlera e kampionuar është
   tashmë vlera e shtypshme dhe nuk ka rrumbullakim që mund ta kalojë
   atë nga një status në tjetrin.

2. Mbulimi. Korpusi duhet të përmbajë vlera kritike dhe vlera të
   painterpretueshme në sasi të mjaftueshme për t'i matur, por jo aq sa
   të bëhet jorealist. Prandaj statusi i synuar zgjidhet i pari dhe
   vlera kampionohet që ta plotësojë atë — jo e kundërta.
"""

from __future__ import annotations

import random
from decimal import ROUND_HALF_UP, Decimal

from analyte.catalog import Analyte, Sex
from analyte.domain.enums import AnalyteStatus
from analyte.grounding.branch_a.classify import classify

DEFAULT_STATUS_WEIGHTS: dict[AnalyteStatus, float] = {
    AnalyteStatus.NORMAL: 0.80,
    AnalyteStatus.LOW: 0.085,
    AnalyteStatus.HIGH: 0.105,
    AnalyteStatus.CRITICAL_LOW: 0.005,
    AnalyteStatus.CRITICAL_HIGH: 0.005,
}
"""Rreth 20% vlera jonormale për analit.

Kjo është më shumë se sa jep një depistim rutinë te një popullatë e
shëndetshme, dhe kjo është me qëllim: një korpus ku pothuajse çdo vlerë
është normale nuk ka mbi çfarë të matë as klasifikimin, as shpjegimin,
as përshkallëzimin kritik. Pasurimi është i njohur dhe raportohet bashkë
me rezultatet; ai nuk duhet ngatërruar me prevalencë."""


def _steps(value: Decimal, decimals: int) -> int:
    """Vlera e shprehur si numër i plotë hapash rrumbullakimi."""
    return int(value.scaleb(decimals).to_integral_value(rounding=ROUND_HALF_UP))


def _value(steps: int, decimals: int) -> Decimal:
    return Decimal(steps).scaleb(-decimals).quantize(Decimal(1).scaleb(-decimals))


def _range_for(analyte: Analyte, sex: Sex, target: AnalyteStatus) -> tuple[int, int] | None:
    """Kufijtë e kampionimit në hapa, ose None nëse statusi s'është i mundur.

    Jo çdo status është i mundur për çdo analit: CRP-ja ka kufi të poshtëm
    zero, prandaj "e ulët" nuk ekziston për të, dhe shumë analite nuk kanë
    prag kritik të përcaktuar.
    """
    low, high = analyte.reference_for(sex)
    if low is None or high is None:
        return None

    d = analyte.decimals
    n_low, n_high = _steps(low, d), _steps(high, d)
    width = max(n_high - n_low, 1)
    n_crit_low = _steps(analyte.critical_low, d) if analyte.critical_low is not None else None
    n_crit_high = _steps(analyte.critical_high, d) if analyte.critical_high is not None else None

    if target is AnalyteStatus.NORMAL:
        return n_low, n_high

    if target is AnalyteStatus.LOW:
        hi = n_low - 1
        lo = max(1, n_low - max(1, (width * 8) // 10))
        if n_crit_low is not None:
            lo = max(lo, n_crit_low + 1)
        return (lo, hi) if lo <= hi else None

    if target is AnalyteStatus.CRITICAL_LOW:
        if n_crit_low is None or n_crit_low < 1:
            return None
        hi = n_crit_low
        # Një e pesta nën pragun: mjaftueshëm poshtë sa të jetë qartë
        # kritike, pa dalë jashtë asaj që një laborator sheh vërtet.
        lo = max(1, n_crit_low - max(1, n_crit_low // 5))
        return (lo, hi)

    if target is AnalyteStatus.HIGH:
        lo = n_high + 1
        hi = n_high + max(1, width)
        if n_crit_high is not None:
            hi = min(hi, n_crit_high - 1)
        return (lo, hi) if lo <= hi else None

    if target is AnalyteStatus.CRITICAL_HIGH:
        if n_crit_high is None:
            return None
        lo = n_crit_high
        hi = n_crit_high + max(1, (n_crit_high - n_high) // 2)
        return (lo, hi)

    return None


def possible_statuses(analyte: Analyte, sex: Sex) -> tuple[AnalyteStatus, ...]:
    """Statuset që mund të prodhohen realisht për këtë analit."""
    return tuple(
        status for status in DEFAULT_STATUS_WEIGHTS if _range_for(analyte, sex, status) is not None
    )


def sample_status(
    rng: random.Random,
    analyte: Analyte,
    sex: Sex,
    weights: dict[AnalyteStatus, float] | None = None,
) -> AnalyteStatus:
    """Zgjedh statusin e synuar.

    Pesha e një statusi të pamundur nuk humbet: ajo i kalon statusit
    fqinj në të njëjtin drejtim, që shkalla e përgjithshme e
    jonormalitetit të mbetet ajo e konfiguruar.
    """
    weights = weights or DEFAULT_STATUS_WEIGHTS
    available = set(possible_statuses(analyte, sex))
    if not available:
        return AnalyteStatus.NORMAL

    redirect = {
        AnalyteStatus.CRITICAL_LOW: AnalyteStatus.LOW,
        AnalyteStatus.CRITICAL_HIGH: AnalyteStatus.HIGH,
        AnalyteStatus.LOW: AnalyteStatus.NORMAL,
        AnalyteStatus.HIGH: AnalyteStatus.NORMAL,
    }

    effective: dict[AnalyteStatus, float] = {s: 0.0 for s in available}
    for status, weight in weights.items():
        target = status
        while target not in available and target in redirect:
            target = redirect[target]
        if target in available:
            effective[target] += weight

    statuses = sorted(effective, key=lambda s: s.value)  # rend i qëndrueshëm
    return rng.choices(statuses, weights=[effective[s] for s in statuses], k=1)[0]


def sample_value(rng: random.Random, analyte: Analyte, sex: Sex, target: AnalyteStatus) -> Decimal:
    """Një vlerë në njësinë kanonike që klasifikohet saktësisht si `target`.

    Kthimi verifikohet me të njëjtin funksion klasifikimi që përdor
    sistemi. Nëse verifikimi do të dështonte, etiketa e së vërtetës bazë
    do të ishte e rreme dhe çdo metrikë e mëpasme e pavlefshme — prandaj
    këtu dështojmë me zë.
    """
    bounds = _range_for(analyte, sex, target)
    if bounds is None:
        raise ValueError(f"{analyte.loinc_code}: statusi {target.value} nuk është i mundur")

    lo, hi = bounds
    if target is AnalyteStatus.NORMAL:
        # Mesatarja e dy kampioneve uniforme: vlerat grumbullohen nga
        # mesi i intervalit, si në popullatë, në vend që të shpërndahen
        # njëtrajtësisht deri te kufijtë.
        steps = (rng.randint(lo, hi) + rng.randint(lo, hi)) // 2
    else:
        steps = rng.randint(lo, hi)

    value = _value(steps, analyte.decimals)
    low, high = analyte.reference_for(sex)
    got = classify(value, low, high, analyte.critical_low, analyte.critical_high).status
    if got is not target:
        raise AssertionError(
            f"{analyte.loinc_code}: u kampionua {value} për {target.value} por doli {got.value}"
        )
    return value


def sample_unreferenced_value(rng: random.Random, analyte: Analyte) -> Decimal:
    """Vlerë e besueshme për një analit pa interval referent.

    Brezi i kampionimit nuk është interval referent dhe nuk kthehet
    askund tjetër: gjetja që del prej kësaj vlere mbetet
    UNINTERPRETABLE, sepse ky është pikërisht rasti i SP5.
    """
    if analyte.sample_low is None or analyte.sample_high is None:
        raise ValueError(f"{analyte.loinc_code}: mungon brezi i kampionimit")

    d = analyte.decimals
    lo, hi = _steps(analyte.sample_low, d), _steps(analyte.sample_high, d)
    return _value(rng.randint(lo, hi), d)
