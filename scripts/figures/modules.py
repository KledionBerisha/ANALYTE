"""
Figura 8 — struktura modulare e aplikacionit.

Varësitë lexohen nga importet e vërteta të `backend/src/analyte`, jo nga një
përshkrim i tyre. Kjo e bën figurën provë: §5.9 pohon se moduli i domenit nuk
varet nga asnjë modul tjetër, dhe këtu ai pohim ose shihet (rreshti i domenit
është bosh) ose e kundërshton vetë figura.

**Pse matricë dhe jo grafik me shigjeta.** Me katërmbëdhjetë module dhe tridhjetë
e një varësi, shigjetat që kapërcejnë shtresa kalojnë pas kutive të tjera dhe
duken të lidhura me modulin e gabuar; heqja e tyre do të fshinte varësi të
vërteta, si `api` → `persistence`. Matrica i tregon të gjitha, me numrin e
deklaratave, dhe e bën ciklin të dukshëm: modulet renditen nga ata që
importojnë më shumë drejt atyre që importohen, prandaj çdo qelizë nën
diagonale është varësi që kthehet mbrapa.
"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from . import layout, style

PACKAGE = Path(__file__).resolve().parents[2] / "backend" / "src" / "analyte"

THESIS_MODULES = (
    "domain", "ingestion", "grounding", "generation",
    "verification", "orchestration", "persistence", "audit",
)
"""Tetë modulet që §5.9 emërton. Të tjerët — `api`, `main`, konfigurimi,
siguria, katalogu, `textnorm` — janë mbështetës dhe vizatohen më të lehtë."""

WIDTH = 6.3


def import_graph(package: Path = PACKAGE) -> Counter[tuple[str, str]]:
    """(importuesi, i importuari) → numri i deklaratave, për modulet e nivelit të parë."""
    edges: Counter[tuple[str, str]] = Counter()
    for path in sorted(package.rglob("*.py")):
        parts = path.relative_to(package).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        source = parts[0]
        file_package = ["analyte", *parts[:-1]]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            for target in _targets(node, file_package):
                if target != source:
                    edges[(source, target)] += 1
    return edges


def _targets(node: ast.AST, file_package: list[str]) -> list[str]:
    if isinstance(node, ast.Import):
        return [a.name.split(".")[1] for a in node.names if a.name.startswith("analyte.")]
    if not isinstance(node, ast.ImportFrom):
        return []
    if node.level == 0:
        base = (node.module or "").split(".")
    else:
        keep = len(file_package) - (node.level - 1)
        base = file_package[:keep] + (node.module.split(".") if node.module else [])
    if not base or base[0] != "analyte":
        return []
    if len(base) >= 2:
        return [base[1]]
    return [a.name for a in node.names]  # `from analyte import x`


def top_level_modules(package: Path = PACKAGE) -> set[str]:
    return {
        p.stem if p.is_file() else p.name
        for p in package.iterdir()
        if not p.name.startswith("__") and (p.is_dir() or p.suffix == ".py")
    }


def build():
    counts = import_graph()
    nodes = sorted(top_level_modules() | {n for edge in counts for n in edge})
    edges = list(counts)
    depth = layout.layers(nodes, edges)
    order = sorted(nodes, key=lambda n: (depth[n], n not in THESIS_MODULES, n))
    index = {name: i for i, name in enumerate(order)}
    cycles = layout.strongly_connected(nodes, edges)
    peak = max(counts.values())

    cell, left, top, right, legend = 0.36, 1.15, 1.0, 0.1, 0.95
    size = cell * len(order)
    width = left + size + right
    height = top + size + legend
    fig, ax = style.canvas(width, height, (0, width), (0, height))

    def center(row: int, col: int) -> tuple[float, float]:
        return left + cell * (col + 0.5), height - top - cell * (row + 0.5)

    for i, name in enumerate(order):
        main = name in THESIS_MODULES
        fill = style.BLUE_TINT if main else style.NEUTRAL
        x, y = center(i, i)
        ax.add_patch(_rect(left - 1.1, y - cell / 2 + 0.02, 1.05, cell - 0.04, fill))
        style.label(ax, left - 0.1, y, name, size=7.5, color=style.INK, ha="right",
                    weight="bold" if main else "normal")
        ax.add_patch(_rect(x - cell / 2 + 0.02, height - top + 0.05, cell - 0.04, 0.9, fill))
        ax.text(x, height - top + 0.5, name, rotation=90, ha="center", va="center", fontsize=7.5,
                color=style.INK, fontweight="bold" if main else "normal", zorder=6)
        # Diagonalja: një modul nuk importon veten.
        ax.add_patch(_rect(x - cell / 2, y - cell / 2, cell, cell, style.NEUTRAL, edge=None))

    for row in range(len(order)):
        for col in range(len(order)):
            x, y = center(row, col)
            if row != col:
                ax.add_patch(_rect(x - cell / 2, y - cell / 2, cell, cell, style.SURFACE,
                                   edge=style.FAINT, lw=0.4))
    for (source, target), count in counts.items():
        row, col = index[source], index[target]
        x, y = center(row, col)
        back = row > col
        strength = count / peak
        fill = _ramp(strength)
        ax.add_patch(_rect(x - cell / 2 + 0.015, y - cell / 2 + 0.015, cell - 0.03, cell - 0.03,
                           fill, edge=style.INK if back else None, lw=1.6, z=4))
        style.label(ax, x, y, str(count), size=7.5, weight="bold",
                    color="#ffffff" if strength > 0.45 else style.INK)

    y = 0.72
    style.label(ax, 0.1, y, "Rreshti importon kolonën; numri është sa deklarata import ka.",
                size=7.2, ha="left")
    style.box(ax, 0.22, y - 0.25, 0.3, 0.2, "", fill=style.BLUE_TINT)
    style.label(ax, 0.45, y - 0.25, "modul i punimit (§5.9)", size=7.2, ha="left")
    style.box(ax, 2.35, y - 0.25, 0.3, 0.2, "", fill=style.NEUTRAL)
    style.label(ax, 2.58, y - 0.25, "modul mbështetës", size=7.2, ha="left")
    ax.add_patch(_rect(4.1, y - 0.35, 0.2, 0.2, style.BLUE_TINT, edge=style.INK, lw=1.6))
    style.label(ax, 4.35, y - 0.25, "varësi që kthehet mbrapa", size=7.2, ha="left")
    if cycles:
        names = " ↔ ".join(sorted(cycles[0]))
        style.label(ax, 0.1, y - 0.5, f"Varësi rrethore mes paketave: {names}.", size=7.2,
                    ha="left", color=style.INK, weight="bold")
    return fig, dict(counts)


def _ramp(strength: float) -> str:
    """Një nuancë blu nga e çelura te e errëta: sa më shumë importe, aq më e errët."""
    low, high = (0xCD, 0xE2, 0xFB), (0x18, 0x4F, 0x95)
    mix = [round(a + (b - a) * strength) for a, b in zip(low, high)]
    return "#{:02x}{:02x}{:02x}".format(*mix)


def _rect(x, y, w, h, fill, *, edge=None, lw=0.8, z=2):
    from matplotlib.patches import Rectangle

    return Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge or "none", linewidth=lw, zorder=z)
