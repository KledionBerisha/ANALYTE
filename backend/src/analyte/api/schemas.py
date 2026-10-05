"""
Format i përgjigjeve të API-së.

**Verifikimi nuk është fushë opsionale.** Çdo përgjigje që mban tekst të
gjeneruar mban edhe `verification: {passed, mode, violation_count,
is_fallback}` (§5 e specifikimit). Ndërfaqja e ndërton treguesin e
transparencës prej saj, dhe fakti që fusha është e detyrueshme në skemë e
bën NFR1 të dukshëm në vetë kontratën e API-së.

**Kufizimet shkojnë me tekstin** (NFR7). `notices` mban çdo gjë që pacienti
duhet ta dijë për besueshmërinë e asaj që lexon — p.sh. që dokumenti u
lexua me OCR — të shkruara nga sistemi, jo nga gjeneruesi.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class RefreshIn(BaseModel):
    refresh_token: str


class RegisterOut(BaseModel):
    """Përgjigjja e regjistrimit dhe e ridërgimit: e njëjtë për çdo email, që të mos tregojë
    nëse ai ka llogari (ADR 0016)."""

    message: str


class EmailIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class ConfirmIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class ResetIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=1, max_length=256)


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MfaChallenge(BaseModel):
    """Përgjigjja e hyrjes kur llogaria ka hap të dytë: fjalëkalimi ishte i saktë, por seanca hapet vetëm pas
    kodit (`POST /auth/login/verify`). Del vetëm pas fjalëkalimit të saktë, prandaj nuk tregon gjë për
    llogaritë e tjera (ADR 0018)."""

    mfa_required: Literal[True] = True
    challenge: str


class LoginVerifyIn(BaseModel):
    challenge: str = Field(min_length=20, max_length=2000)
    code: str = Field(min_length=1, max_length=64)
    """Kodi me gjashtë shifra i aplikacionit, ose një kod rimëkëmbjeje."""


class CodeIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class DisableTwoFactorIn(BaseModel):
    password: str = Field(min_length=1, max_length=256)
    code: str = Field(min_length=1, max_length=64)
    """Kodi i aplikacionit ose një kod rimëkëmbjeje."""


class TwoFactorStatus(BaseModel):
    enabled: bool
    recovery_codes_remaining: int


class TwoFactorEnrollment(BaseModel):
    """Sekreti dhe URI-ja e aplikacionit. Shfaqen vetëm këtu, një herë; pasi regjistrimi të konfirmohet nuk lexohen më."""

    secret: str
    otpauth_uri: str


class RecoveryCodes(BaseModel):
    """Kodet e rimëkëmbjes. Shfaqen vetëm një herë: shërbimi mban vetëm HMAC-in e tyre."""

    recovery_codes: list[str]


class UserOut(BaseModel):
    id: UUID
    email: str
    created_at: datetime


class UploadOut(BaseModel):
    id: UUID
    job_id: UUID
    state: str
    model_consent: bool
    """Pëlqimi që u ruajt vërtet: `false` kur shërbimi nuk e ka modelin të ndezur, edhe nëse klienti dërgoi `true`."""


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    uploaded_at: datetime
    size_bytes: int
    state: str
    state_reason: str
    channel: str | None
    terminal: bool
    model_consent: bool


class DocumentPage(BaseModel):
    items: list[DocumentOut]
    total: int
    limit: int
    offset: int


class TransitionOut(BaseModel):
    source: str
    target: str
    reason: str
    attempt: int | None
    at: str


class JobOut(BaseModel):
    started_at: datetime | None
    finished_at: datetime | None
    failed: bool


class StatusOut(BaseModel):
    id: UUID
    state: str
    reason: str
    terminal: bool
    job: JobOut | None
    transitions: list[TransitionOut]


class VerificationSummary(BaseModel):
    passed: bool
    mode: str
    violation_count: int
    is_fallback: bool


class Notice(BaseModel):
    """Një kufizim i shprehur nga sistemi. `code` e lejon ndërfaqen ta vendosë
    aty ku duhet — njoftimi i OCR-së në krye, jo i humbur në fund."""

    code: str
    text: str


class ExplanationOut(BaseModel):
    document_id: UUID
    text: str
    generator: str
    critical: bool
    banner: str | None
    """SP4 — teksti i njoftimit kur ka vlera kritike. Ndërfaqja e shfaq para
    shpjegimit, si element më vete, dhe jo të humbur brenda tekstit."""
    disclaimer: str
    notices: list[Notice]
    verification: VerificationSummary


class ViolationOut(BaseModel):
    type: str
    detected_by: str
    sentence: str
    evidence: str
    confidence: float | None


class VerificationDetail(BaseModel):
    passed: bool
    mode: str
    rules_version: str
    classifier_version: str | None
    duration_ms: int
    violations: list[ViolationOut]


class AttemptOut(BaseModel):
    attempt: int
    generator: str
    is_fallback: bool
    delivered: bool
    failed: bool
    verification: VerificationDetail | None


class VerificationOut(BaseModel):
    document_id: UUID
    verification: VerificationSummary
    attempts: list[AttemptOut]


class TermOut(BaseModel):
    term: str
    explanation_sq: str
    category: str | None
    synonyms: list[str]
    source_ref: str
