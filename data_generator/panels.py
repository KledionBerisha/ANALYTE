"""
Panelet e analizave dhe përbërja e një porosie laboratorike.

Një raport real nuk është listë e rastësishme analitesh: mjeku porosit
panele. Kjo ka rëndësi për nxjerrjen, sepse panelet krijojnë bllokun
vizual që Dega A duhet të segmentojë, dhe për vlerësimin, sepse
shpërndarja e analiteve nëpër dokumente nuk është uniforme.
"""

from __future__ import annotations

import random

from .catalog import Analyte, load_analytes, load_analytes_without_reference

PANEL_TITLES: dict[str, str] = {
    "hematologji": "HEMOGRAMË E PLOTË",
    "biokimi": "BIOKIMI BAZË",
    "elektrolite": "ELEKTROLITE",
    "melcia": "PROFILI HEPATIK",
    "veshkat": "FUNKSIONI RENAL",
    "lipide": "PROFILI LIPIDIK",
    "tiroide": "FUNKSIONI I TIROIDES",
    "hekuri": "STATUSI I HEKURIT",
    "inflamacion": "TREGUES INFLAMACIONI",
    "vitamina": "VITAMINA",
    "speciale": "ANALIZA TË VEÇANTA",
}

PANEL_ORDER: tuple[str, ...] = tuple(PANEL_TITLES)

CORE_PANELS: tuple[str, ...] = ("hematologji", "biokimi", "elektrolite")
"""Panelet që shfaqen në shumicën e porosive rutinë."""

OPTIONAL_PANELS: tuple[tuple[str, float], ...] = (
    ("melcia", 0.55),
    ("veshkat", 0.50),
    ("lipide", 0.45),
    ("tiroide", 0.30),
    ("hekuri", 0.25),
    ("inflamacion", 0.35),
    ("vitamina", 0.20),
)
"""Panele shtesë me gjasën e tyre të porositjes."""


def analytes_in_panel(panel: str) -> tuple[Analyte, ...]:
    return tuple(a for a in load_analytes() if a.panel == panel)


def sample_panels(rng: random.Random) -> tuple[str, ...]:
    """Zgjedh panelet e një porosie.

    Gjithmonë të paktën një panel bazë, që dokumenti të mos dalë bosh.
    """
    chosen = [p for p in CORE_PANELS if rng.random() < 0.8]
    if not chosen:
        chosen = [rng.choice(CORE_PANELS)]
    chosen += [p for p, prob in OPTIONAL_PANELS if rng.random() < prob]
    return tuple(p for p in PANEL_ORDER if p in set(chosen))


def compose_order(
    rng: random.Random,
    *,
    dropout: float = 0.12,
    extra_probability: float = 0.25,
) -> tuple[tuple[str, tuple[Analyte, ...]], ...]:
    """Analitet e shtypura, të grupuara sipas panelit.

    `dropout` heq analite të veçuara nga një panel: laboratorët nuk i
    shtypin gjithmonë të gjitha rreshtat e një paneli, dhe nxjerrja nuk
    duhet të mësojë të presë gjatësi fikse.

    `extra_probability` shton analite pa interval referent në tabelën e
    brendshme — lënda e parë e SP5.
    """
    groups: list[tuple[str, tuple[Analyte, ...]]] = []
    for panel in sample_panels(rng):
        members = tuple(a for a in analytes_in_panel(panel) if rng.random() > dropout)
        if members:
            groups.append((panel, members))

    if not groups:  # dropout-i i hoqi të gjitha; mbaj një panel të plotë
        panel = rng.choice(CORE_PANELS)
        groups.append((panel, analytes_in_panel(panel)))

    if rng.random() < extra_probability:
        pool = load_analytes_without_reference()
        count = rng.randint(1, 2)
        picked = tuple(rng.sample(pool, k=min(count, len(pool))))
        picked = tuple(sorted(picked, key=lambda a: a.loinc_code))
        groups.append(("speciale", picked))

    return tuple(groups)
