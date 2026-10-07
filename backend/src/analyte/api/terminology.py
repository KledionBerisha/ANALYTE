"""
Fjalori publik — nga `resources/terminology.csv`, burimi i vetëm.

"""

from __future__ import annotations

from fastapi import APIRouter

from analyte.catalog import load_terminology, terms_by_name
from analyte.textnorm import fold

from .problems import Problem
from .schemas import TermOut

router = APIRouter(prefix="/terminology", tags=["terminology"])


def _out(term) -> TermOut:
    return TermOut(
        term=term.term,
        explanation_sq=term.explanation_sq,
        category=term.category,
        synonyms=list(term.synonyms),
        source_ref=term.source_ref,
    )


@router.get("", response_model=list[TermOut])
def glossary() -> list[TermOut]:
    return [_out(t) for t in load_terminology()]


@router.get("/{term}", response_model=TermOut)
def lookup(term: str) -> TermOut:
    wanted = fold(term)
    for entry in terms_by_name().values():
        if wanted in {fold(form) for form in entry.surface_forms()}:
            return _out(entry)
    raise Problem(404, "Termi nuk gjendet në fjalor")
