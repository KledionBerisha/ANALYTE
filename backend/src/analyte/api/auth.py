"""
Regjistrimi, hyrja dhe rifreskimi.

Hyrja e dështuar ka një përgjigje të vetme, qoftë email-i i panjohur apo
fjalëkalimi i gabuar: dy përgjigje të ndryshme do t'i tregonin kujtdo se
cili email ka llogari. Kufizimi i shpeshtësisë së përpjekjeve nuk është
ndërtuar ende dhe shënohet te ADR 0013.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.persistence.tables import UserRow
from analyte.security import TokenError, hash_password, issue_token, read_token, verify_password

from . import deps
from .problems import Problem
from .schemas import Credentials, RefreshIn, Tokens, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

_DECOY_HASH = hash_password("fjalëkalim-i-rremë-vetëm-për-kohën")
"""Kur email-i nuk ekziston, fjalëkalimi krahasohet me këtë. Pa të, hyrja
me email të panjohur do të ishte dukshëm më e shpejtë — Argon2 është i
ngadalshëm me qëllim — dhe koha do të tregonte atë që mesazhi e fsheh."""


def _normalize(email: str) -> str:
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    if not local or "." not in domain or " " in email:
        raise Problem(422, "Email i pavlefshëm")
    return email


def _tokens(user: UserRow, config: Settings) -> Tokens:
    return Tokens(
        access_token=issue_token(
            user.id, "access", timedelta(minutes=config.access_token_minutes), config.jwt_secret
        ),
        refresh_token=issue_token(
            user.id, "refresh", timedelta(days=config.refresh_token_days), config.jwt_secret
        ),
    )


@router.post("/register", response_model=UserOut, status_code=201)
def register(
    body: Credentials,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> UserOut:
    email = _normalize(body.email)
    if len(body.password) < config.min_password_length:
        raise Problem(
            422, "Fjalëkalim shumë i shkurtër", f"të paktën {config.min_password_length} shenja"
        )
    user = UserRow(email=email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise Problem(409, "Ky email ka tashmë llogari") from None
    audit.user_registered(db, user.id)
    return UserOut(id=user.id, email=user.email, created_at=user.created_at)


@router.post("/login", response_model=Tokens)
def login(
    body: Credentials,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> Tokens:
    user = db.scalars(select(UserRow).where(UserRow.email == body.email.strip().lower())).first()
    stored = user.password_hash if user is not None else _DECOY_HASH
    if not verify_password(stored, body.password) or user is None:
        raise Problem(401, "Email ose fjalëkalim i gabuar")
    return _tokens(user, config)


@router.post("/refresh", response_model=Tokens)
def refresh(
    body: RefreshIn,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> Tokens:
    try:
        user_id = read_token(body.refresh_token, "refresh", config.jwt_secret)
    except TokenError:
        raise Problem(401, "Token rifreskimi i pavlefshëm ose i skaduar") from None
    user = db.get(UserRow, user_id)
    if user is None:
        raise Problem(401, "Token rifreskimi i pavlefshëm ose i skaduar")
    return _tokens(user, config)


@router.get("/me", response_model=UserOut)
def me(user: UserRow = Depends(deps.current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, created_at=user.created_at)
