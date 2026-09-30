"""
Figura 6 — makina e gjendjeve e përpunimit të dokumentit.

Gjendjet dhe kalimet lexohen nga `TRANSITIONS` (`orchestration/states.py`),
që është vetë tabela që sistemi zbaton. Vendosja në faqe është e vetmja gjë e
shkruar me dorë, dhe `build` refuzon të vizatojë nëse një gjendje e re nuk ka
vend — kështu figura nuk mund të heqë një gjendje pa u vënë re.
"""

from __future__ import annotations

from analyte.domain.enums import ProcessingState as S
from analyte.orchestration.states import TRANSITIONS

from . import layout, style

STEP = 1.0
"""Largësia vertikale ndërmjet gjendjeve të shtegut kryesor."""

POSITIONS: dict[S, tuple[float, float]] = {
    # shtegu kryesor, lart-poshtë
    S.UPLOADED: (0.0, 0.0),
    S.INGESTING: (0.0, -1.0),
    S.TEXT_EXTRACTED: (0.0, -2.0),
    S.PARSING: (0.0, -3.0),
    S.GROUNDED: (0.0, -4.0),
    S.GENERATING: (0.0, -5.0),
    S.VERIFYING: (0.0, -6.0),
    S.DELIVERED: (0.0, -7.0),
    # dega e OCR-së, djathtas
    S.OCR_RUNNING: (2.3, -1.5),
    S.FAILED_INGESTION: (2.3, -2.6),
    # daljet pa sukses, majtas
    S.REJECTED: (-2.3, -0.5),
    S.NO_FINDINGS: (-2.3, -3.5),
    # shablloni rezervë, djathtas
    S.TEMPLATE_FALLBACK: (2.3, -6.0),
}


UNSUCCESSFUL = {S.REJECTED, S.FAILED_INGESTION, S.NO_FINDINGS}
"""Gjendje përfundimtare ku pacienti nuk merr shpjegim. Dallohen me kornizë
me vija; `DELIVERED` është e vetmja përfundimtare me shpjegim."""

WIDTH, HEIGHT = 6.3, 7.9


def check_positions() -> None:
    missing = set(TRANSITIONS) - set(POSITIONS)
    extra = set(POSITIONS) - set(TRANSITIONS)
    if missing or extra:
        raise ValueError(
            "Figura 6 nuk përputhet me TRANSITIONS — "
            f"pa vend: {sorted(s.value for s in missing)}; "
            f"pa gjendje: {sorted(s.value for s in extra)}"
        )


def edges() -> list[tuple[S, S]]:
    return [(a, b) for a, targets in TRANSITIONS.items() for b in sorted(targets, key=list(S).index)]


def build():
    check_positions()
    fig, ax = style.canvas(WIDTH, HEIGHT, (-3.4, 3.4), (-8.25, 0.55))

    boxes: dict[S, style.Box] = {}
    for state, (x, y) in POSITIONS.items():
        terminal = not TRANSITIONS[state]
        unsuccessful = state in UNSUCCESSFUL
        boxes[state] = style.box(
            ax, x, y, 1.75, 0.5, state.name,
            fill=style.NEUTRAL if unsuccessful else (style.BLUE_TINT if terminal else style.SURFACE),
            edge=style.INK,
            ls="--" if unsuccessful else "-",
            double=terminal,
            size=8,
            weight="bold" if state in (S.UPLOADED, S.DELIVERED) else "normal",
        )

    _, back = layout.split_back_edges(list(TRANSITIONS), edges())
    for source, target in edges():
        if (source, target) in back:
            continue
        a, b = boxes[source], boxes[target]
        # Dy kalimet që kalojnë pranë kutive të tjera lakohen pak, që të mos preken.
        bend = 0.0
        if {source, target} == {S.GENERATING, S.TEMPLATE_FALLBACK}:
            bend = 0.12
        if {source, target} == {S.TEMPLATE_FALLBACK, S.DELIVERED}:
            bend = 0.12
        style.connect(ax, a, b, rad=bend)

    for source, target in back:
        a, b = boxes[source], boxes[target]
        if source is target:
            # Sytha: GENERATING → GENERATING (gjeneruesi hedh përjashtim).
            style.arrow(ax, (a.right, a.cy + 0.13), (a.right, a.cy - 0.13), rad=-1.8)
            style.label(ax, a.right + 0.42, a.cy, "përjashtim:\nriprovim", size=7, ha="left")
        else:
            # Rigjenerimi: VERIFYING → GENERATING, në të majtë të shtegut kryesor.
            start = (a.left, a.cy + 0.05)
            end = (b.left, b.cy - 0.05)
            style.arrow(ax, start, end, rad=-0.9)
            style.label(ax, a.left - 0.55, (a.cy + b.cy) / 2, "shkelje:\nrigjenerim", size=7, ha="right")

    _legend(ax)
    return fig, edges()


def _legend(ax) -> None:
    y = -7.85
    items = (
        (-2.85, "gjendje e ndërmjetme", dict(fill=style.SURFACE)),
        (-0.55, "përfundimtare", dict(fill=style.BLUE_TINT, double=True)),
        (1.55, "pa shpjegim", dict(fill=style.NEUTRAL, ls="--", double=True)),
    )
    for x, text, options in items:
        style.box(ax, x, y, 0.42, 0.26, "", **options)
        style.label(ax, x + 0.3, y, text, size=7.5, ha="left")
