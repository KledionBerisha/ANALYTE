"""
Konteksti i nxjerrë: gjetjet, pohimet, krahasimet e kryqëzuar.

Kthehen modelet e domenit ashtu siç janë, me numrat dhjetorë si varg —
Pydantic-u i serializon kështu — që ndërfaqja të shfaqë saktësisht vlerën
që u verifikua dhe jo një përafrim me presje lundruese.

Para gjendjes përfundimtare këto pika kthejnë 409: konteksti shkruhet në
bazë bashkë me gjendjen përfundimtare, dhe një listë bosh gjatë përpunimit
do të dukej si "nuk ka gjetje".
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from analyte.domain.enums import ProcessingState
from analyte.domain.models import AnalyteFinding, CrossReference, GroundingContext, ReportAssertion
from analyte.persistence import repository
from analyte.persistence.tables import DocumentRow

from . import deps
from .problems import Problem

router = APIRouter(prefix="/documents/{document_id}", tags=["findings"])


def finished_context(
    document: DocumentRow = Depends(deps.owned_document),
    db: Session = Depends(deps.session),
) -> GroundingContext:
    if not ProcessingState(document.state).is_terminal:
        raise Problem(409, "Dokumenti ende po përpunohet", f"gjendja: {document.state}")
    return repository.load_context(db, document.id)


@router.get("/findings", response_model=list[AnalyteFinding])
def findings(context: GroundingContext = Depends(finished_context)) -> tuple[AnalyteFinding, ...]:
    return context.findings


@router.get("/assertions", response_model=list[ReportAssertion])
def assertions(
    context: GroundingContext = Depends(finished_context),
) -> tuple[ReportAssertion, ...]:
    return context.assertions


@router.get("/cross-refs", response_model=list[CrossReference])
def cross_refs(context: GroundingContext = Depends(finished_context)) -> tuple[CrossReference, ...]:
    return context.cross_refs
