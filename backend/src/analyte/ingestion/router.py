"""
Vendimi: shtresë teksti apo OCR.

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .pdf_text import PageText, read_pdf

MIN_CHARACTERS_PER_PAGE = 200
"""Nën këtë prag faqja nuk quhet e lexuar nga shtresa e tekstit."""

MIN_ROWS_PER_PAGE = 8
"""Një faqe raporti ka dhjetëra rreshta; pak rreshta do të thotë mbetje
teksti mbi një fotografi, jo dokument dixhital."""


class Channel(str, Enum):
    """Nga cila rrugë erdhi teksti. Raportohet krahas çdo rezultati."""

    TEXT_LAYER = "text_layer"
    OCR = "ocr"


@dataclass(frozen=True, slots=True)
class Routing:
    """Vendimi bashkë me atë që u lexua për ta marrë."""

    channel: Channel
    pages: tuple[PageText, ...]
    reason: str

    @property
    def has_text(self) -> bool:
        return self.channel is Channel.TEXT_LAYER


def route(path: Path) -> Routing:
    """Lexon dokumentin dhe vendos se cila rrugë e përpunon."""
    pages = read_pdf(path)
    if not pages:
        return Routing(Channel.OCR, pages, "dokumenti nuk ka asnjë faqe të lexueshme")

    usable = [
        page
        for page in pages
        if page.character_count >= MIN_CHARACTERS_PER_PAGE and len(page.rows) >= MIN_ROWS_PER_PAGE
    ]
    if not usable:
        return Routing(Channel.OCR, pages, "asnjë faqe nuk ka shtresë teksti të përdorshme")

    # Mjafton që faqja e parë me përmbajtje të jetë e lexueshme: dokumentet
    # e përziera — faqe dixhitale dhe faqe të skanuara bashkë — janë të
    # rralla dhe do të trajtoheshin gabim nga çdo vendim i vetëm.
    return Routing(Channel.TEXT_LAYER, pages, f"{len(usable)}/{len(pages)} faqe me tekst")
