"""
Varësitë e pikave fundore: sesioni, përdoruesi, dokumenti i tij.

Dokumenti i një përdoruesi tjetër kthehet si 404, jo 403. Një 403 do të
pohonte se dokumenti ekziston — dhe identifikuesit e dokumenteve nuk
duhet të zbulojnë asgjë për askënd tjetër.
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from analyte.config import Settings
from analyte.persistence.tables import DocumentRow, UserRow
from analyte.security import TokenError, read_token

from .problems import Problem

_bearer = HTTPBearer(auto_error=False)


def settings(request: Request) -> Settings:
    return request.app.state.settings


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


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(session),
    config: Settings = Depends(settings),
) -> UserRow:
    if credentials is None:
        raise Problem(401, "Kërkohet hyrja")
    try:
        user_id = read_token(credentials.credentials, "access", config.jwt_secret)
    except TokenError:
        raise Problem(401, "Token i pavlefshëm ose i skaduar") from None
    user = db.get(UserRow, user_id)
    if user is None:
        raise Problem(401, "Token i pavlefshëm ose i skaduar")
    return user


def owned_document(
    document_id: UUID,
    user: UserRow = Depends(current_user),
    db: Session = Depends(session),
) -> DocumentRow:
    document = db.get(DocumentRow, document_id)
    if document is None or document.user_id != user.id:
        raise Problem(404, "Dokumenti nuk u gjet")
    return document
