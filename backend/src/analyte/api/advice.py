"""
Tabela publike e këshillave me burim — nga `resources/advice.csv`, burimi i vetëm (ADR 0023).

Nuk kërkon hyrje: tabela nuk mban të dhëna të askujt. Kthehet e plotë, edhe rreshtat e paplotësuar
(`is_filled: false`): fshehja e tyre do ta paraqiste tabelën më të plotë seç është. Pacientit i shfaqen
vetëm rreshtat e plotësuar.
"""

from __future__ import annotations

from fastapi import APIRouter

from analyte.catalog import analytes_by_code, load_advice

from .schemas import AdviceOut

router = APIRouter(prefix="/advice", tags=["advice"])


@router.get("", response_model=list[AdviceOut])
def table() -> list[AdviceOut]:
    names = analytes_by_code()
    return [
        AdviceOut(
            loinc_code=a.loinc_code,
            analyte_name_sq=names[a.loinc_code].name_canonical_sq,
            direction=a.direction,
            advice_sq=a.advice_sq,
            source_ref=a.source_ref,
            is_filled=a.is_filled,
        )
        for a in load_advice()
    ]
