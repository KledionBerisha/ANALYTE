"""
Fjalëkalimet dhe tokenët.

Argon2id për fjalëkalimet — algoritmi i rekomanduar sot, me parametrat e
parazgjedhur të `argon2-cffi`. JWT me HS256 për hyrjen: një token aksesi
jetëshkurtër dhe një token rifreskimi, të dalluar nga fusha `typ` që njëri
të mos pranohet në vend të tjetrit.

Tokenët nuk mbajnë asgjë përveç identifikuesit të përdoruesit dhe kohëve.
Email-i nuk hyn: tokeni lexohet nga kushdo që e mban, dhe email-i është e
dhënë personale.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

ALGORITHM = "HS256"
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


class TokenError(ValueError):
    """Tokeni mungon, ka skaduar, ose nuk është i llojit të kërkuar."""


def issue_token(user_id: UUID, kind: str, lifetime: timedelta, secret: str) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "typ": kind, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def read_token(token: str, kind: str, secret: str) -> UUID:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as error:
        raise TokenError(str(error)) from None
    if payload.get("typ") != kind:
        raise TokenError(f"pritej token '{kind}'")
    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError):
        raise TokenError("token pa përdorues") from None
