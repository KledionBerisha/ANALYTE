"""
Leximi i shtresës së tekstit të një PDF-je, me pozicione.

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from analyte.domain.models import BoundingBox

ROW_TOLERANCE = 3.0
"""Sa pikë mund të ndryshojë vija bazë brenda të njëjtit rresht."""


@dataclass(frozen=True, slots=True)
class TextFragment:
    """Një varg i vetëm teksti bashkë me vendin ku është shtypur."""

    text: str
    bbox: BoundingBox

    @property
    def x0(self) -> float:
        return self.bbox.x0

    @property
    def baseline(self) -> float:
        """Buza e poshtme — më e qëndrueshme se ajo e sipërme kur
        madhësitë e shkronjave ndryshojnë brenda rreshtit."""
        return self.bbox.y1


@dataclass(frozen=True, slots=True)
class TextRow:
    """Fragmentet që ndodhen në të njëjtën vijë bazë, nga e majta djathtas."""

    page: int
    fragments: tuple[TextFragment, ...]

    @property
    def text(self) -> str:
        return " ".join(fragment.text for fragment in self.fragments)

    @property
    def bbox(self) -> BoundingBox:
        return BoundingBox(
            x0=min(f.bbox.x0 for f in self.fragments),
            y0=min(f.bbox.y0 for f in self.fragments),
            x1=max(f.bbox.x1 for f in self.fragments),
            y1=max(f.bbox.y1 for f in self.fragments),
        )


@dataclass(frozen=True, slots=True)
class PageText:
    """Një faqe e lexuar."""

    number: int
    rows: tuple[TextRow, ...]
    ocr: bool = False
    """Faqja u lexua me OCR, jo nga shtresa e tekstit. OCR-ja humb presje dhjetore; teksti i PDF-së jo (ADR 0020)."""

    @property
    def character_count(self) -> int:
        return sum(len(row.text) for row in self.rows)


def read_pdf(path: Path) -> tuple[PageText, ...]:
    """Lexon të gjitha faqet e një PDF-je.

    Një faqe pa shtresë teksti kthehet me zero rreshta dhe jo si gabim:
    vendimi nëse duhet OCR i takon router-it, jo lexuesit.
    """
    pages: list[PageText] = []
    with pymupdf.open(path) as document:
        for index, page in enumerate(document, start=1):
            pages.append(PageText(number=index, rows=_rows_of(page, index)))
    return tuple(pages)


def _rows_of(page: pymupdf.Page, number: int) -> tuple[TextRow, ...]:
    fragments = [
        TextFragment(text=text, bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1))
        for x0, y0, x1, y1, text, *_ in _raw_lines(page)
        if text.strip()
    ]
    return group_into_rows(fragments, number)


def _raw_lines(page: pymupdf.Page) -> list[tuple[float, float, float, float, str]]:
    out = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", ()):
            text = "".join(span["text"] for span in line["spans"]).strip()
            if text:
                x0, y0, x1, y1 = line["bbox"]
                out.append((x0, y0, x1, y1, text))
    return out


def group_into_rows(fragments: list[TextFragment], page: int) -> tuple[TextRow, ...]:
    """Bashkon fragmentet në rreshta sipas vijës bazë.

    Ndarja bëhet e para sipas y-së dhe pastaj brenda rreshtit sipas x-së.
    Rendi horizontal ka rëndësi: nxjerrësi mbështetet te ai për të ditur
    se emri i analitit vjen para vlerës së tij.
    """
    rows: list[list[TextFragment]] = []
    for fragment in sorted(fragments, key=lambda f: (f.baseline, f.x0)):
        if rows and abs(rows[-1][0].baseline - fragment.baseline) <= ROW_TOLERANCE:
            rows[-1].append(fragment)
        else:
            rows.append([fragment])

    return tuple(
        TextRow(page=page, fragments=tuple(sorted(row, key=lambda f: f.x0))) for row in rows
    )
