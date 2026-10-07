"""
Fleta e burimeve që mungojnë: lista duhet të jetë e plotë, të mos shpikë burime,
dhe të heqë zërat sapo të kenë burim.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from analyte.catalog import Pattern, Term, load_patterns, load_terminology

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import build_source_worksheets as sheets  # noqa: E402


def test_the_worksheet_lists_exactly_the_terms_and_patterns_that_still_have_a_placeholder():
    text = sheets.build()
    for term in load_terminology():
        assert (f"| {term.term} |" in text) is sheets.is_placeholder(term.source_ref)
    for pattern in load_patterns():
        assert (f"| {pattern.pattern_id} |" in text) is sheets.is_placeholder(pattern.source_ref)
    terms, patterns = sheets.pending_terms(), sheets.pending_patterns()
    assert f"**{len(terms)}** terma dhe **{len(patterns)}** kombinime" in text


def test_the_worksheet_invents_no_source():
    text = sheets.build().lower()
    for marker in ("doi:", "http://", "https://", "et al", "pmid"):
        assert marker not in text


def test_a_filled_source_removes_the_entry_from_the_worksheet(monkeypatch):
    terms = (
        Term("anemi", "nivel i ulët i hemoglobinës", "Burim i lexuar nga autori", "gjendje", ()),
        Term("leukopeni", "numër i ulët i bardhëzave", "[BURIMI — plotësohet]", "gjendje", ()),
    )
    patterns = (Pattern("P01", (("718-7", "decreased"),), "[REFERENCË — plotësohet]"),)
    monkeypatch.setattr(sheets, "load_terminology", lambda: terms)
    monkeypatch.setattr(sheets, "load_patterns", lambda: patterns)
    text = sheets.build()
    assert "| leukopeni |" in text and "| anemi |" not in text
    assert "**1** terma dhe **1** kombinime" in text


@pytest.mark.parametrize(
    ("source", "pending"),
    [("", True), ("[BURIMI — plotësohet gjatë ndërtimit]", True), ("[REFERENCË — plotësohet]", True), ("Burim i vërtetë", False)],
)
def test_placeholder_detection(source, pending):
    assert sheets.is_placeholder(source) is pending
