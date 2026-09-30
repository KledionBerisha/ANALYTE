"""
Fjalëkalimet dhe tokenët.

Argon2id për fjalëkalimet — algoritmi i rekomanduar sot, me parametrat e
parazgjedhur të `argon2-cffi`. JWT me HS256 për hyrjen: një token aksesi
jetëshkurtër dhe një token rifreskimi, të dalluar nga fusha `typ` që njëri
të mos pranohet në vend të tjetrit.

Tokenët nuk mbajnë asgjë përveç identifikuesve dhe kohëve. Email-i nuk hyn:
tokeni lexohet nga kushdo që e mban, dhe email-i është e dhënë personale.

Çdo token i përket një seance (`sid`) që shërbimi mund ta revokojë, dhe
tokeni i rifreskimit mban edhe identifikuesin e vet (`jti`), që përdoret
vetëm një herë (ADR 0014). Një token pa këto fusha — i lëshuar para ADR 0014
— refuzohet, jo pranohet si i vlefshëm.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

ALGORITHM = "HS256"
_hasher = PasswordHasher()


def keyed_hash(secret: str, label: str, value: str) -> str:
    """HMAC i një vlere personale, me etiketë që ndan përdorimet.

    Tabela e kufizimit të hyrjeve duhet të dallojë një email ose një adresë
    IP nga një tjetër, por nuk ka pse t'i mbajë ato. Me çelës, hash-i nuk
    kthehet nga dikush që lexon bazën dhe provon email-e të njohur; etiketa
    garanton që hash-i i një email-i nuk përputhet me atë të një IP-je.
    """
    digest = hmac.new(secret.encode(), f"{label}\0{value}".encode(), hashlib.sha256)
    return digest.hexdigest()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


class TokenError(ValueError):
    """Tokeni mungon, ka skaduar, ose nuk është i llojit të kërkuar."""


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: UUID
    session_id: UUID
    token_id: UUID | None
    """`jti`; e ka vetëm tokeni i rifreskimit."""


def issue_token(
    user_id: UUID,
    kind: str,
    lifetime: timedelta,
    secret: str,
    *,
    session_id: UUID,
    token_id: UUID | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "typ": kind,
        "sid": str(session_id),
        "iat": now,
        "exp": now + lifetime,
    }
    if token_id is not None:
        payload["jti"] = str(token_id)
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def read_token(token: str, kind: str, secret: str) -> TokenClaims:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as error:
        raise TokenError(str(error)) from None
    if payload.get("typ") != kind:
        raise TokenError(f"pritej token '{kind}'")
    try:
        user_id = UUID(payload["sub"])
        session_id = UUID(payload["sid"])
        token_id = UUID(payload["jti"]) if kind == "refresh" else None
    except (KeyError, ValueError):
        raise TokenError("token pa përdorues, seancë ose identifikues") from None
    return TokenClaims(user_id, session_id, token_id)
