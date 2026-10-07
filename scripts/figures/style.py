"""
Stili i përbashkët i figurave.

"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

INK = "#0b0b0b"
MUTED = "#52514e"
FAINT = "#9a9993"
SURFACE = "#ffffff"
NEUTRAL = "#f0efec"
BLUE = "#2a78d6"
BLUE_DEEP = "#184f95"
BLUE_TINT = "#cde2fb"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
    }
)


@dataclass(frozen=True, slots=True)
class Box:
    """Një drejtkëndësh i vizatuar; mban gjeometrinë që skajet e përdorin."""

    cx: float
    cy: float
    w: float
    h: float

    @property
    def left(self) -> float:
        return self.cx - self.w / 2

    @property
    def right(self) -> float:
        return self.cx + self.w / 2

    @property
    def top(self) -> float:
        return self.cy + self.h / 2

    @property
    def bottom(self) -> float:
        return self.cy - self.h / 2

    def anchor(self, toward: tuple[float, float]) -> tuple[float, float]:
        """Pika ku drejtëza nga qendra drejt `toward` del nga kufiri i kutisë."""
        dx, dy = toward[0] - self.cx, toward[1] - self.cy
        if dx == 0 and dy == 0:
            return self.cx, self.cy
        scale = min(
            (self.w / 2) / abs(dx) if dx else math.inf,
            (self.h / 2) / abs(dy) if dy else math.inf,
        )
        return self.cx + dx * scale, self.cy + dy * scale


def canvas(width: float, height: float, xlim: tuple[float, float], ylim: tuple[float, float]):
    """Figurë me boshte në njësi të të dhënave, pa kornizë. `aspect=equal`: një
    njësi është e njëjtë në të dy drejtimet, që kutitë të mos deformohen."""
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    return fig, ax


def box(
    ax: Axes,
    cx: float,
    cy: float,
    w: float,
    h: float,
    text: str = "",
    *,
    fill: str = SURFACE,
    edge: str = INK,
    lw: float = 1.2,
    ls: str = "-",
    size: float = 9,
    color: str = INK,
    weight: str = "normal",
    double: bool = False,
    align: str = "center",
    mono: bool = False,
    z: int = 3,
) -> Box:
    ax.add_patch(
        FancyBboxPatch(
            (cx - w / 2, cy - h / 2),
            w,
            h,
            boxstyle="round,pad=0,rounding_size=0.07",
            facecolor=fill,
            edgecolor=edge,
            linewidth=lw,
            linestyle=ls,
            zorder=z,
        )
    )
    if double:
        inset = 0.06
        ax.add_patch(
            FancyBboxPatch(
                (cx - w / 2 + inset, cy - h / 2 + inset),
                w - 2 * inset,
                h - 2 * inset,
                boxstyle="round,pad=0,rounding_size=0.04",
                facecolor="none",
                edgecolor=edge,
                linewidth=lw * 0.8,
                zorder=z,
            )
        )
    if text:
        x = {"center": cx, "left": cx - w / 2 + 0.08}[align]
        ax.text(
            x,
            cy,
            text,
            ha=align,
            va="center",
            fontsize=size,
            color=color,
            fontweight=weight,
            family="DejaVu Sans Mono" if mono else "DejaVu Sans",
            zorder=z + 1,
            linespacing=1.3,
        )
    return Box(cx, cy, w, h)


def arrow(
    ax: Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = INK,
    lw: float = 1.3,
    ls: str = "-",
    rad: float = 0.0,
    head: bool = True,
    z: int = 2,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-|>,head_length=5,head_width=2.6" if head else "-",
            color=color,
            linewidth=lw,
            linestyle=ls,
            shrinkA=0,
            shrinkB=0,
            zorder=z,
        )
    )


def connect(
    ax: Axes,
    a: Box,
    b: Box,
    *,
    rad: float = 0.0,
    **style,
) -> None:
    """Shigjetë nga kutia `a` te `b`, nga kufijtë e tyre e jo nga qendrat."""
    start = a.anchor((b.cx, b.cy))
    end = b.anchor((a.cx, a.cy))
    arrow(ax, start, end, rad=rad, **style)


def label(
    ax: Axes,
    x: float,
    y: float,
    text: str,
    *,
    size: float = 8,
    color: str = MUTED,
    ha: str = "center",
    va: str = "center",
    weight: str = "normal",
    style: str = "normal",
) -> None:
    ax.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        fontsize=size,
        color=color,
        fontweight=weight,
        fontstyle=style,
        zorder=6,
    )


def save(fig: Figure, directory: Path, name: str) -> list[Path]:
    """PNG për Word, SVG për rishikim; PNG-ja në 300 dpi, sa një faqe e shtypur."""
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for suffix, options in ((".png", {"dpi": 300}), (".svg", {})):
        path = directory / f"{name}{suffix}"
        fig.savefig(path, **options)
        written.append(path)
    plt.close(fig)
    return written
