"""
Tabelat e bazës së të dhënave (§4 e specifikimit).

Tabelat pasqyrojnë modelet e domenit fushë për fushë, që një kontekst i
ruajtur dhe i lexuar sërish të jetë i barabartë me origjinalin — testi i
kthimit e kontrollon këtë. Identifikuesit e gjetjeve dhe të pohimeve
ruhen ata të domenit, sepse krahasimet e kryqëzuar dhe kombinimet u
referohen atyre.

**Numrat dhjetorë ruhen si tekst i saktë.** Rregulli R1 krahason numrat me
barazi të saktë, dhe SQLite — ku ekzekutohen testet — e kthen `Numeric`-un
në numër me presje lundruese. `ExactDecimal` e ruan vargun e `Decimal`-it
dhe e kthen të njëjtin `Decimal`, në çdo bazë.

**Çfarë nuk është këtu.** Terminologjia dhe intervalet referente mbeten te
`resources/`, burimi i vetëm i së vërtetës; një kopje në bazë do të fillonte
të largohej prej tij. Tabelat e bisedës dhe të ekzekutimeve të vlerësimit
shtohen bashkë me veçoritë e tyre.

**Emri i skedarit është i koduar.** Pacientët i emërtojnë skedarët me
emrin e tyre; kolona mban tekstin e koduar, jo emrin (NFR5).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    TypeDecorator,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(UTC)


class ExactDecimal(TypeDecorator):
    """`Decimal` i ruajtur si varg, pa humbje në asnjë bazë."""

    impl = String(64)
    cache_ok = True

    def process_bind_param(self, value: Decimal | None, dialect) -> str | None:
        return None if value is None else format(value, "f")

    def process_result_value(self, value: str | None, dialect) -> Decimal | None:
        return None if value is None else Decimal(value)


class UtcDateTime(TypeDecorator):
    """Kohë gjithmonë në UTC. SQLite nuk ruan zonën; kjo e rikthen."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("koha duhet të ketë zonë")
        return value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_now)


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    mime: Mapped[str] = mapped_column(String(100))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_now)
    channel: Mapped[str | None] = mapped_column(String(20))
    state: Mapped[str] = mapped_column(String(30))
    """Gjendja e fundit, e shkruar me çdo kalim — burimi i `/status`."""
    state_reason: Mapped[str] = mapped_column(Text, default="")

    jobs: Mapped[list[JobRow]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class JobRow(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    state: Mapped[str] = mapped_column(String(30))
    attempt: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_now)
    started_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    error: Mapped[str | None] = mapped_column(Text)

    document: Mapped[DocumentRow] = relationship(back_populates="jobs")


def _document_fk() -> Any:
    return mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)


class FindingRow(Base):
    __tablename__ = "lab_findings"
    __table_args__ = (Index("ix_lab_findings_document_analyte", "document_id", "analyte_code"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    analyte_code: Mapped[str] = mapped_column(String(20))
    analyte_name_raw: Mapped[str] = mapped_column(String(200))
    analyte_name_canonical: Mapped[str] = mapped_column(String(200))
    value_raw: Mapped[str] = mapped_column(String(64))
    value: Mapped[Decimal] = mapped_column(ExactDecimal)
    unit_raw: Mapped[str | None] = mapped_column(String(40))
    unit_canonical: Mapped[str] = mapped_column(String(40))
    value_canonical: Mapped[Decimal] = mapped_column(ExactDecimal)
    ref_low: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    ref_high: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    ref_source: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    severity: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    page: Mapped[int] = mapped_column(Integer)
    bbox: Mapped[dict | None] = mapped_column(JSON)
    measured_at: Mapped[date | None] = mapped_column(Date)
    flag_in_document: Mapped[str | None] = mapped_column(String(10))


class AssertionRow(Base):
    __tablename__ = "report_assertions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    document_id: Mapped[UUID] = _document_fk()
    position: Mapped[int] = mapped_column(Integer)
    text_span: Mapped[str] = mapped_column(Text)
    analyte_code: Mapped[str | None] = mapped_column(String(20))
    direction: Mapped[str] = mapped_column(String(20))
    polarity: Mapped[str] = mapped_column(String(20))
    certainty: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(20))
    char_start: Mapped[int] = mapped_column(Integer)
    char_end: Mapped[int] = mapped_column(Integer)


class CrossReferenceRow(Base):
    __tablename__ = "cross_references"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    document_id: Mapped[UUID] = _document_fk()
    position: Mapped[int] = mapped_column(Integer)
    analyte_code: Mapped[str] = mapped_column(String(20))
    state: Mapped[str] = mapped_column(String(30))
    assertion_id: Mapped[UUID | None] = mapped_column(Uuid)
    finding_id: Mapped[UUID | None] = mapped_column(Uuid)


class GlossaryRow(Base):
    """Zërat e fjalorit ashtu siç ishin kur u ndërtua konteksti.

    Ruhen të plotë dhe jo si referencë te tabela: nëse shpjegimi ndryshon
    më vonë, shpjegimi që pa pacienti mbetet i gjurmueshëm.
    """

    __tablename__ = "document_glossary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[UUID] = _document_fk()
    position: Mapped[int] = mapped_column(Integer)
    term: Mapped[str] = mapped_column(String(200))
    explanation_sq: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    synonyms: Mapped[list] = mapped_column(JSON, default=list)


class UnexplainedTermRow(Base):
    __tablename__ = "document_unexplained_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[UUID] = _document_fk()
    position: Mapped[int] = mapped_column(Integer)
    term: Mapped[str] = mapped_column(String(200))


class PatternRow(Base):
    __tablename__ = "pattern_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[UUID] = _document_fk()
    position: Mapped[int] = mapped_column(Integer)
    pattern_id: Mapped[str] = mapped_column(String(20))
    finding_ids: Mapped[list] = mapped_column(JSON)
    source_ref: Mapped[str] = mapped_column(Text)


class ExplanationRow(Base):
    """Një përpjekje gjenerimi, ose shablloni rezervë.

    `raw_output` është ajo që prodhoi gjeneruesi; `final_output` është ajo
    që pa pacienti, dhe mbushet vetëm te rreshti i dorëzuar. Dallimi mes
    tyre është gjurma e NFR1.
    """

    __tablename__ = "explanations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = _document_fk()
    attempt: Mapped[int] = mapped_column(Integer)
    generator: Mapped[str] = mapped_column(String(200))
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    raw_output: Mapped[str | None] = mapped_column(Text)
    final_output: Mapped[str | None] = mapped_column(Text)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_now)

    verification: Mapped[VerificationRow | None] = relationship(
        back_populates="explanation", cascade="all, delete-orphan", uselist=False
    )


class VerificationRow(Base):
    __tablename__ = "verification_results"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    explanation_id: Mapped[UUID] = mapped_column(
        ForeignKey("explanations.id", ondelete="CASCADE"), unique=True
    )
    mode: Mapped[str] = mapped_column(String(30))
    passed: Mapped[bool] = mapped_column(Boolean)
    rules_version: Mapped[str] = mapped_column(String(20))
    classifier_version: Mapped[str | None] = mapped_column(String(200))
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_now)

    explanation: Mapped[ExplanationRow] = relationship(back_populates="verification")
    violations: Mapped[list[ViolationRow]] = relationship(
        back_populates="verification", cascade="all, delete-orphan", order_by="ViolationRow.position"
    )


class ViolationRow(Base):
    __tablename__ = "violations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    verification_result_id: Mapped[UUID] = mapped_column(
        ForeignKey("verification_results.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(40))
    detected_by: Mapped[str] = mapped_column(String(20))
    sentence: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    verification: Mapped[VerificationRow] = relationship(back_populates="violations")


class AuditEventRow(Base):
    """Ngjarjet e auditimit (NFR2).

    `document_id` nuk është çelës i huaj me qëllim: kur pacienti e fshin
    dokumentin, të dhënat e tij shkojnë, por gjurma që ai u përpunua dhe u
    fshi mbetet. Prandaj ngarkesa nuk mban kurrë të dhëna shëndetësore as
    emra — vetëm gjendje, numërime dhe arsye teknike.
    """

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_document_created", "document_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[UUID | None] = mapped_column(Uuid)
    user_id: Mapped[UUID | None] = mapped_column(Uuid)
    event_type: Mapped[str] = mapped_column(String(60))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=_now)
