"""
Varësitë e pikave fundore: sesioni, përdoruesi, dokumenti i tij.

Dokumenti i një përdoruesi tjetër kthehet si 404, jo 403. Një 403 do të
pohonte se dokumenti ekziston — dhe identifikuesit e dokumenteve nuk
duhet të zbulojnë asgjë për askënd tjetër.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from analyte.config import Settings
from analyte.mail import Mailer
from analyte.persistence.tables import AuthSessionRow, DocumentRow, UserRow
from analyte.security import TokenError, read_token

from .problems import Problem

_bearer = HTTPBearer(auto_error=False)


def settings(request: Request) -> Settings:
    return request.app.state.settings


def mailer(request: Request) -> Mailer:
    return request.app.state.mailer


def session(request: Request) -> Iterator[Session]:
    db = request.app.state.sessions()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class Login(NamedTuple):
    user: UserRow
    auth_session: AuthSessionRow


def current_login(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(session),
    config: Settings = Depends(settings),
) -> Login:
    """Përdoruesi dhe seanca e tokenit të aksesit.

    Seanca kontrollohet në çdo kërkesë, jo vetëm nënshkrimi i tokenit: një
    seancë e revokuar (dalje, ose ripërdorim i tokenit të rifreskimit) nuk
    duhet të mbetet e përdorshme deri në skadimin e tokenit të aksesit
    (ADR 0014).
    """
    if credentials is None:
        raise Problem(401, "Kërkohet hyrja")
    try:
        claims = read_token(credentials.credentials, "access", config.jwt_secret)
    except TokenError:
        raise Problem(401, "Token i pavlefshëm ose i skaduar") from None
    auth_session = db.get(AuthSessionRow, claims.session_id)
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or auth_session.user_id != claims.user_id
    ):
        raise Problem(401, "Token i pavlefshëm ose i skaduar")
    user = db.get(UserRow, claims.user_id)
    if user is None:
        raise Problem(401, "Token i pavlefshëm ose i skaduar")
    return Login(user, auth_session)


def current_user(login: Login = Depends(current_login)) -> UserRow:
    return login.user


def owned_document(
    document_id: UUID,
    user: UserRow = Depends(current_user),
    db: Session = Depends(session),
) -> DocumentRow:
    document = db.get(DocumentRow, document_id)
    if document is None or document.user_id != user.id:
        raise Problem(404, "Dokumenti nuk u gjet")
    return document
