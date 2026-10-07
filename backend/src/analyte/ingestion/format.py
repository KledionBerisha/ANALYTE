"""
Kontrolli i formatit: degëzimi UPLOADED → REJECTED.

"""

from __future__ import annotations

from pathlib import Path

import pymupdf

PDF_MAGIC = b"%PDF-"
HEADER_WINDOW = 1024
"""Standardi e lejon kokën e PDF-së brenda 1024 bajtëve të parë; disa
programe shkruajnë mbeturina para saj, dhe lexuesit e pranojnë."""


def rejection_reason(path: Path) -> str | None:
    """Pse skedari nuk mund të përpunohet, ose `None` nëse mundet."""
    try:
        with path.open("rb") as handle:
            header = handle.read(HEADER_WINDOW)
    except OSError as error:
        return f"skedari nuk lexohet: {error}"

    if PDF_MAGIC not in header:
        return "skedari nuk është PDF"

    try:
        with pymupdf.open(path) as document:
            if document.needs_pass:
                return "PDF-ja është e mbrojtur me fjalëkalim"
            if document.page_count == 0:
                return "PDF-ja nuk ka asnjë faqe"
    except Exception as error:  # pymupdf nuk ka hierarki të qëndrueshme gabimesh
        return f"PDF-ja është e dëmtuar: {error}"

    return None
