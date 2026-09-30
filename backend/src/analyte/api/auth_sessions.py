"""
Seancat e revokueshme dhe rrotullimi i tokenëve të rifreskimit (ADR 0014).

Hyrja hap një seancë. Çdo rifreskim e shpenzon tokenin që u përdor dhe jep
një të ri në të njëjtën seancë, kështu që një token rifreskimi vlen një
herë. Nëse një token i shpenzuar paraqitet sërish, dikush ka dy kopje të
tij — përdoruesi dhe dikush tjetër — dhe shërbimi nuk ka si të dijë cili
është cili. Revokon gjithë seancën: të dy humbasin aksesin dhe përdoruesi
hyn sërish.

Revokimi vlen menjëherë edhe për tokenin e aksesit, sepse `current_login`
kontrollon seancën në çdo kërkesë. Pa këtë, një seancë e revokuar do të
mbetej e përdorshme deri në skadimin e tokenit të aksesit.

**Dritarja e hirit.** Dy rifreskime paralele të të njëjtit klient — një
faqe që ngarkon disa gjëra me një token të skaduar — do të dukeshin si
ripërdorim. Brenda `refresh_reuse_grace_seconds` tokeni i shpenzuar
refuzohet pa e revokuar seancën. Kjo nuk i jep asgjë një vjedhësi: ai merr
401 njësoj, nuk merr token të ri.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.persistence.tables import AuthSessionRow, RefreshTokenRow, UserRow
from analyte.security import TokenClaims, issue_token

from .problems import Problem
from .schemas import Tokens


def _invalid() -> Problem:
    return Problem(401, "Token rifreskimi i pavlefshëm ose i skaduar")


def _issue(db: Session, auth_session: AuthSessionRow, config: Settings, now: datetime) -> Tokens:
    token_id = uuid4()
    db.add(
        RefreshTokenRow(
            id=token_id,
            session_id=auth_session.id,
            expires_at=now + timedelta(days=config.refresh_token_days),
        )
    )
    user_id = auth_session.user_id
    return Tokens(
        access_token=issue_token(
            user_id,
            "access",
            timedelta(minutes=config.access_token_minutes),
            config.jwt_secret,
            session_id=auth_session.id,
        ),
        refresh_token=issue_token(
            user_id,
            "refresh",
            timedelta(days=config.refresh_token_days),
            config.jwt_secret,
            session_id=auth_session.id,
            token_id=token_id,
        ),
    )


def open_session(db: Session, user: UserRow, config: Settings, now: datetime) -> Tokens:
    # Tokenët e skaduar nuk përdoren më; fshihen këtu që tabela të mos rritet.
    db.execute(delete(RefreshTokenRow).where(RefreshTokenRow.expires_at < now))
    auth_session = AuthSessionRow(user_id=user.id, created_at=now)
    db.add(auth_session)
    db.flush()
    return _issue(db, auth_session, config, now)


def rotate(db: Session, claims: TokenClaims, config: Settings, now: datetime) -> Tokens:
    auth_session = db.get(AuthSessionRow, claims.session_id)
    token = db.get(RefreshTokenRow, claims.token_id) if claims.token_id else None
    if (
        auth_session is None
        or token is None
        or token.session_id != auth_session.id
        or auth_session.user_id != claims.user_id
        or auth_session.revoked_at is not None
    ):
        raise _invalid()

    # Shpenzimi është një UPDATE i kushtëzuar: nëse dy kërkesa e lexojnë
    # tokenin si të papërdorur në të njëjtin çast, vetëm njëra e fiton.
    spent = db.execute(
        update(RefreshTokenRow)
        .where(RefreshTokenRow.id == token.id, RefreshTokenRow.used_at.is_(None))
        .values(used_at=now)
    ).rowcount
    if spent == 0:
        db.refresh(token)
        grace = timedelta(seconds=config.refresh_reuse_grace_seconds)
        if token.used_at is not None and now - token.used_at <= grace:
            raise _invalid()
        revoke(db, auth_session, "refresh_reuse", now)
        # I ruajtur para 401-it: sesioni i kërkesës e kthen prapa çdo gjë kur
        # kërkesa përfundon me përjashtim, dhe revokimi nuk duhet humbur.
        db.commit()
        raise _invalid()
    return _issue(db, auth_session, config, now)


def revoke(db: Session, auth_session: AuthSessionRow, reason: str, now: datetime) -> None:
    if auth_session.revoked_at is not None:
        return
    auth_session.revoked_at = now
    auth_session.revoked_reason = reason
    audit.session_revoked(db, auth_session.user_id, reason)
