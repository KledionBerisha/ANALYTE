"""
Biseda mbi dokumentin — ende e pandërtuar.

Biseda kërkon model gjuhësor, dhe modeli mungon me vendim të autorit
(2026-09-27). Pikat fundore ekzistojnë që kontrata e API-së të jetë e
plotë, dhe kthejnë 501 me arsyen, jo një përgjigje të rreme.
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
