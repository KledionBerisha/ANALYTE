"""
Chatbot mbi dokumentin — ende e pandërtuar.

"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from analyte.persistence.tables import DocumentRow

from . import deps
from .problems import Problem

router = APIRouter(prefix="/documents/{document_id}/chat", tags=["chat"])


@router.post("")
@router.get("")
def chat(document: DocumentRow = Depends(deps.owned_document)) -> None:
    raise Problem(501, "Biseda nuk është ndërtuar ende", "kërkon modelin gjuhësor")
