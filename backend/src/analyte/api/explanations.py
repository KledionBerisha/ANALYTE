"""
Shpjegimi i dorëzuar dhe verifikimi i tij.

`/explanation` kthen vetëm tekstin që pa pacienti — drafti i pranuar ose
shablloni — bashkë me përmbledhjen e verifikimit. `/verification` kthen
çdo përpjekje, të dorëzuar apo jo, me shkeljet e saj: tekstet e refuzuara
nuk shfaqen si shpjegim, por gjurma e tyre është e hapur për pronarin.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from analyte.domain.enums import AnalyteStatus, ProcessingState
from analyte.domain.models import GroundingContext
from analyte.domain.policy import CRITICAL_BANNER_SQ, DISCLAIMER_SQ
from analyte.generation.templates import TemplateGenerator
from analyte.persistence import repository
from analyte.persistence.tables import DocumentRow, ExplanationRow, VerificationRow

from . import deps
from .problems import Problem
from .schemas import (
    AttemptOut,
    ExplanationOut,
    Notice,
    VerificationDetail,
    VerificationOut,
    VerificationSummary,
    ViolationOut,
)

router = APIRouter(prefix="/documents/{document_id}", tags=["explanations"])

OCR_NOTICE_SQ = (
    "Ky dokument u lexua nga një fotografi e skanuar. Disa vlera mund të jenë "
    "lexuar gabim; krahasojini me dokumentin origjinal para se të mbështeteni tek to."
)
MODEL_NOTICE_SQ = (
    "Ky shpjegim u shkrua nga një model gjuhësor dhe u kontrollua automatikisht kundrejt vlerave të nxjerra nga dokumenti. "
    "Kontrolli kap vetëm një pjesë të gabimeve të mundshme: krahasojeni me dokumentin origjinal dhe flisni me mjekun para se të mbështeteni tek ai."
)
MODEL_DECLINED_NOTICE_SQ = (
    "Ky shpjegim u shkrua me shabllonin e sistemit, jo me një model gjuhësor, sepse nuk dhatë pëlqimin për dërgimin e "
    "përmbajtjes së dokumentit te ofruesi i modelit. Për këtë dokument nuk iu dërgua asnjë kërkesë ofruesit."
)
MODEL_WITHHELD_NOTICE_SQ = (
    "Ky shpjegim u shkrua me shabllonin e sistemit, jo me një model gjuhësor, edhe pse dhatë pëlqimin: pjesë të "
    "dokumentit duken se përmbajnë të dhëna personale ({kinds}), dhe ato nuk i dërgohen ofruesit të modelit. "
    "Për këtë dokument nuk iu dërgua asnjë kërkesë ofruesit. Kontrolli është i përafërt dhe mund të shënojë edhe tekst pa të dhëna personale."
)
GATE_KIND_SQ = {
    "name_like": "emër ose fjalë me shkronjë të madhe që sistemi nuk e njeh",
    "title": "titull si Dr. ose Prof.",
    "date": "datë",
    "birth_or_age": "moshë ose datëlindje",
    "phone": "numër telefoni",
    "email": "adresë email",
    "url": "adresë interneti",
    "long_number": "numër i gjatë, p.sh. numër dosjeje",
    "id_token": "identifikues",
    "address_cue": "adresë",
    "contact_cue": "të dhëna kontakti",
    "uncatalogued": "vlerë e paparashikuar",
}
"""Kategoritë që porta e çidentifikimit (`generation.deidentify`) mund të shënojë, ashtu si u thuhen pacientit. Kurrë
vargu i shënuar: njoftimi nuk duhet ta përsërisë të dhënën që po e mbron."""
FALLBACK_NOTICE_SQ = (
    "Shpjegimi i gjeneruar nuk kaloi kontrollin automatik; po shfaqet shpjegimi "
    "i thjeshtë i sistemit."
)


def _delivered(document: DocumentRow, db: Session) -> ExplanationRow:
    if document.state != ProcessingState.DELIVERED.value:
        detail = f"gjendja: {document.state}"
        if ProcessingState(document.state).is_terminal:
            raise Problem(409, "Ky dokument nuk ka shpjegim", detail)
        raise Problem(409, "Dokumenti ende po përpunohet", detail)
    row = repository.load_delivered(db, document.id)
    if row is None or row.verification is None:  # pragma: no cover - mbrojtje e integritetit
        raise Problem(500, "Shpjegimi i dorëzuar mungon")
    return row


def _summary(row: ExplanationRow) -> VerificationSummary:
    verification: VerificationRow = row.verification
    return VerificationSummary(
        passed=verification.passed,
        mode=verification.mode,
        violation_count=len(verification.violations),
        is_fallback=row.is_fallback,
    )


def notices(document: DocumentRow, context: GroundingContext, row: ExplanationRow) -> list[Notice]:
    """Kufizimet që pacienti duhet t'i dijë (NFR7), të shkruara nga sistemi."""
    out = []
    if document.channel == "ocr":
        out.append(Notice(code="ocr", text=OCR_NOTICE_SQ))
    uninterpretable = sum(1 for f in context.findings if f.status is AnalyteStatus.UNINTERPRETABLE)
    if uninterpretable:
        out.append(
            Notice(
                code="uninterpretable",
                text=f"{uninterpretable} vlera nuk u interpretuan sepse nuk u gjet interval referent.",
            )
        )
    if context.unexplained_terms:
        out.append(
            Notice(
                code="unexplained_terms",
                text=f"Raporti përmend {len(context.unexplained_terms)} terma që sistemi nuk i shpjegon.",
            )
        )
    if document.model_use == "no_consent":
        out.append(Notice(code="model_declined", text=MODEL_DECLINED_NOTICE_SQ))
    elif document.model_use == "identifying_content":
        kinds = [
            GATE_KIND_SQ[k]
            for k in (document.model_gate_kinds or "").split(",")
            if k in GATE_KIND_SQ
        ]
        out.append(
            Notice(
                code="model_withheld",
                text=MODEL_WITHHELD_NOTICE_SQ.format(kinds=", ".join(kinds) or "të paklasifikuara"),
            )
        )
    if row.is_fallback:
        out.append(Notice(code="fallback", text=FALLBACK_NOTICE_SQ))
    elif row.generator != TemplateGenerator.name:
        # Teksti i dorëzuar është i një modeli gjuhësor (ADR 0017); shablloni, dhe shablloni rezervë, nuk e kanë këtë njoftim.
        out.append(Notice(code="model", text=MODEL_NOTICE_SQ))
    return out


@router.get("/explanation", response_model=ExplanationOut)
def explanation(
    document: DocumentRow = Depends(deps.owned_document),
    db: Session = Depends(deps.session),
) -> ExplanationOut:
    row = _delivered(document, db)
    context = repository.load_context(db, document.id)
    return ExplanationOut(
        document_id=document.id,
        text=row.final_output,
        generator=row.generator,
        critical=bool(context.critical_findings()),
        banner=CRITICAL_BANNER_SQ if context.critical_findings() else None,
        disclaimer=DISCLAIMER_SQ,
        notices=notices(document, context, row),
        verification=_summary(row),
    )


@router.get("/verification", response_model=VerificationOut)
def verification(
    document: DocumentRow = Depends(deps.owned_document),
    db: Session = Depends(deps.session),
) -> VerificationOut:
    delivered = _delivered(document, db)
    attempts = []
    for row in repository.load_attempts(db, document.id):
        detail = None
        if row.verification is not None:
            v = row.verification
            detail = VerificationDetail(
                passed=v.passed,
                mode=v.mode,
                rules_version=v.rules_version,
                classifier_version=v.classifier_version,
                duration_ms=v.duration_ms,
                violations=[
                    ViolationOut(
                        type=x.type,
                        detected_by=x.detected_by,
                        sentence=x.sentence,
                        evidence=x.evidence,
                        confidence=x.confidence,
                    )
                    for x in v.violations
                ],
            )
        attempts.append(
            AttemptOut(
                attempt=row.attempt,
                generator=row.generator,
                is_fallback=row.is_fallback,
                delivered=row.delivered,
                failed=row.error is not None,
                verification=detail,
            )
        )
    return VerificationOut(
        document_id=document.id, verification=_summary(delivered), attempts=attempts
    )
