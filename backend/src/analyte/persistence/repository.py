"""
Kalimi ndërmjet modeleve të domenit dhe rreshtave të bazës.

Domeni nuk di për bazën (ADR 0001); ky modul është i vetmi vend ku të dyja
takohen. Çdo gjë që shkruhet këtu lexohet sërish si i njëjti objekt domeni
— identifikuesit, numrat dhjetorë dhe rendi përfshirë — dhe testi i
kthimit e kontrollon këtë fushë për fushë. Rendi ruhet me kolonë të veçantë
sepse baza nuk premton asnjë rend, ndërsa shablloni dhe verifikimi varen
prej tij.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from analyte.domain.models import (
    AdviceEntry,
    AnalyteFinding,
    BoundingBox,
    CrossReference,
    GlossaryEntry,
    GroundingContext,
    PatternObservation,
    ReportAssertion,
    VerificationResult,
    Violation,
)
from analyte.domain.processing import Delivery, Explanation

from .tables import (
    AdviceRow,
    AssertionRow,
    CrossReferenceRow,
    ExplanationRow,
    FindingRow,
    GlossaryRow,
    PatternRow,
    UnexplainedTermRow,
    VerificationRow,
    ViolationRow,
)

CONTEXT_TABLES = (
    FindingRow,
    AssertionRow,
    CrossReferenceRow,
    GlossaryRow,
    UnexplainedTermRow,
    PatternRow,
    AdviceRow,
)


# --------------------------------------------------------------------
# Konteksti
# --------------------------------------------------------------------


def save_context(session: Session, context: GroundingContext) -> None:
    """Shkruan kontekstin, duke zëvendësuar çdo version të mëparshëm."""
    document_id = context.document_id
    for table in CONTEXT_TABLES:
        session.execute(delete(table).where(table.document_id == document_id))

    for position, f in enumerate(context.findings):
        session.add(
            FindingRow(
                id=f.id,
                document_id=document_id,
                position=position,
                analyte_code=f.analyte_code,
                analyte_name_raw=f.analyte_name_raw,
                analyte_name_canonical=f.analyte_name_canonical,
                value_raw=f.value_raw,
                value=f.value,
                unit_raw=f.unit_raw,
                unit_canonical=f.unit_canonical,
                value_canonical=f.value_canonical,
                ref_low=f.ref_low,
                ref_high=f.ref_high,
                ref_source=f.ref_source.value,
                status=f.status.value,
                severity=f.severity,
                page=f.page,
                bbox=f.bbox.model_dump() if f.bbox else None,
                measured_at=f.measured_at,
                flag_in_document=f.flag_in_document,
            )
        )
    for position, a in enumerate(context.assertions):
        session.add(
            AssertionRow(
                id=a.id,
                document_id=document_id,
                position=position,
                text_span=a.text_span,
                analyte_code=a.analyte_code,
                direction=a.direction.value,
                polarity=a.polarity.value,
                certainty=a.certainty.value,
                kind=a.kind.value,
                char_start=a.char_start,
                char_end=a.char_end,
            )
        )
    for position, r in enumerate(context.cross_refs):
        session.add(
            CrossReferenceRow(
                id=r.id,
                document_id=document_id,
                position=position,
                analyte_code=r.analyte_code,
                state=r.state.value,
                assertion_id=r.assertion_id,
                finding_id=r.finding_id,
            )
        )
    for position, e in enumerate(context.glossary):
        session.add(
            GlossaryRow(
                document_id=document_id,
                position=position,
                term=e.term,
                explanation_sq=e.explanation_sq,
                source_ref=e.source_ref,
                category=e.category,
                synonyms=list(e.synonyms),
            )
        )
    for position, term in enumerate(context.unexplained_terms):
        session.add(UnexplainedTermRow(document_id=document_id, position=position, term=term))
    for position, p in enumerate(context.patterns):
        session.add(
            PatternRow(
                document_id=document_id,
                position=position,
                pattern_id=p.pattern_id,
                finding_ids=[str(i) for i in p.finding_ids],
                source_ref=p.source_ref,
            )
        )
    for position, e in enumerate(context.advice):
        session.add(
            AdviceRow(
                document_id=document_id,
                position=position,
                finding_id=e.finding_id,
                analyte_code=e.analyte_code,
                direction=e.direction.value,
                advice_sq=e.advice_sq,
                source_ref=e.source_ref,
            )
        )
    session.flush()


def _rows(session: Session, table, document_id: UUID):
    return session.scalars(
        select(table).where(table.document_id == document_id).order_by(table.position)
    ).all()


def load_context(session: Session, document_id: UUID) -> GroundingContext:
    """Konteksti i ruajtur; bosh nëse dokumenti nuk arriti te bazimi."""
    findings = tuple(
        AnalyteFinding(
            id=r.id,
            analyte_code=r.analyte_code,
            analyte_name_raw=r.analyte_name_raw,
            analyte_name_canonical=r.analyte_name_canonical,
            value_raw=r.value_raw,
            value=r.value,
            unit_raw=r.unit_raw,
            unit_canonical=r.unit_canonical,
            value_canonical=r.value_canonical,
            ref_low=r.ref_low,
            ref_high=r.ref_high,
            ref_source=r.ref_source,
            status=r.status,
            severity=r.severity,
            page=r.page,
            bbox=BoundingBox(**r.bbox) if r.bbox else None,
            measured_at=r.measured_at,
            flag_in_document=r.flag_in_document,
        )
        for r in _rows(session, FindingRow, document_id)
    )
    assertions = tuple(
        ReportAssertion(
            id=r.id,
            text_span=r.text_span,
            analyte_code=r.analyte_code,
            direction=r.direction,
            polarity=r.polarity,
            certainty=r.certainty,
            kind=r.kind,
            char_start=r.char_start,
            char_end=r.char_end,
        )
        for r in _rows(session, AssertionRow, document_id)
    )
    return GroundingContext(
        document_id=document_id,
        findings=findings,
        assertions=assertions,
        cross_refs=tuple(
            CrossReference(
                id=r.id,
                analyte_code=r.analyte_code,
                state=r.state,
                assertion_id=r.assertion_id,
                finding_id=r.finding_id,
            )
            for r in _rows(session, CrossReferenceRow, document_id)
        ),
        glossary=tuple(
            GlossaryEntry(
                term=r.term,
                explanation_sq=r.explanation_sq,
                source_ref=r.source_ref,
                category=r.category,
                synonyms=tuple(r.synonyms or ()),
            )
            for r in _rows(session, GlossaryRow, document_id)
        ),
        unexplained_terms=tuple(r.term for r in _rows(session, UnexplainedTermRow, document_id)),
        patterns=tuple(
            PatternObservation(
                pattern_id=r.pattern_id,
                finding_ids=tuple(UUID(i) for i in r.finding_ids),
                source_ref=r.source_ref,
            )
            for r in _rows(session, PatternRow, document_id)
        ),
        advice=tuple(
            AdviceEntry(
                finding_id=r.finding_id,
                analyte_code=r.analyte_code,
                direction=r.direction,
                advice_sq=r.advice_sq,
                source_ref=r.source_ref,
            )
            for r in _rows(session, AdviceRow, document_id)
        ),
    )


# --------------------------------------------------------------------
# Shpjegimi dhe verifikimi
# --------------------------------------------------------------------


def _verification_row(result: VerificationResult) -> VerificationRow:
    return VerificationRow(
        id=result.id,
        mode="rules" if result.classifier_version is None else "rules+classifier",
        passed=result.passed,
        rules_version=result.rules_version,
        classifier_version=result.classifier_version,
        duration_ms=result.duration_ms,
        created_at=result.created_at,
        violations=[
            ViolationRow(
                id=v.id,
                position=position,
                type=v.type.value,
                detected_by=v.detected_by.value,
                sentence=v.sentence,
                evidence=v.evidence,
                confidence=v.confidence,
            )
            for position, v in enumerate(result.violations)
        ],
    )


def save_explanation(session: Session, document_id: UUID, explanation: Explanation) -> None:
    """Çdo përpjekje një rresht; shablloni rezervë, kur ka, një rresht më shumë."""
    generated = explanation.delivery is Delivery.GENERATED
    for attempt in explanation.attempts:
        delivered = generated and attempt.passed and attempt.text == explanation.text
        row = ExplanationRow(
            document_id=document_id,
            attempt=attempt.number,
            generator=attempt.generator,
            raw_output=attempt.text,
            final_output=attempt.text if delivered else None,
            delivered=delivered,
            error=attempt.error,
        )
        if attempt.verification is not None:
            row.verification = _verification_row(attempt.verification)
        session.add(row)

    if not generated:
        row = ExplanationRow(
            document_id=document_id,
            attempt=len(explanation.attempts) + 1,
            generator="template",
            raw_output=explanation.text,
            final_output=explanation.text,
            is_fallback=True,
            delivered=True,
        )
        row.verification = _verification_row(explanation.verification)
        session.add(row)
    session.flush()


def load_attempts(session: Session, document_id: UUID) -> list[ExplanationRow]:
    return list(
        session.scalars(
            select(ExplanationRow)
            .where(ExplanationRow.document_id == document_id)
            .order_by(ExplanationRow.attempt)
        ).all()
    )


def load_delivered(session: Session, document_id: UUID) -> ExplanationRow | None:
    return session.scalars(
        select(ExplanationRow).where(
            ExplanationRow.document_id == document_id, ExplanationRow.delivered.is_(True)
        )
    ).first()


def to_verification(row: VerificationRow) -> VerificationResult:
    return VerificationResult(
        id=row.id,
        explanation_id=row.explanation_id,
        violations=tuple(
            Violation(
                id=v.id,
                type=v.type,
                detected_by=v.detected_by,
                sentence=v.sentence,
                evidence=v.evidence,
                confidence=v.confidence,
            )
            for v in row.violations
        ),
        rules_version=row.rules_version,
        classifier_version=row.classifier_version,
        duration_ms=row.duration_ms,
        created_at=row.created_at,
    )
