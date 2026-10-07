"""
Hapi i dytë i hyrjes: kodet njëpërdorimshe të kohës (TOTP) dhe kodet e rimëkëmbjes (ADR 0018).

"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
from urllib.parse import quote

PERIOD = 30
DIGITS = 6
WINDOW = 1
SECRET_BYTES = 20
"""Gjatësia e sekretit të rekomanduar nga RFC 4226 për SHA-1: 160 bit."""

_RECOVERY_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
"""32 shenja pa `i`, `l`, `o`, `u`, që të mos ngatërrohen kur kopjohen me dorë: 5 bit për shenjë."""
_RECOVERY_LENGTH = 10


def new_secret() -> str:
    """Sekreti i ri, base32 pa mbushje (kështu e kërkojnë aplikacionet)."""
    return base64.b32encode(secrets.token_bytes(SECRET_BYTES)).decode().rstrip("=")


def _key(secret: str) -> bytes:
    cleaned = secret.replace(" ", "").upper()
    return base64.b32decode(cleaned + "=" * (-len(cleaned) % 8))


def hotp(key: bytes, counter: int, digits: int = DIGITS) -> str:
    """HOTP sipas RFC 4226, §5.3: ndërprerje dinamike mbi HMAC-SHA-1."""
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    number = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(number % 10**digits).zfill(digits)


def step_of(now: float, period: int = PERIOD) -> int:
    return int(now // period)


def code_at(secret: str, step: int, digits: int = DIGITS) -> str:
    return hotp(_key(secret), step, digits)


def match(secret: str, code: str, now: float, window: int = WINDOW) -> int | None:
    """Hapi me të cilin përputhet kodi brenda dritares, ose `None`.

    Kontrollon çdo hap të dritares pa dalë herët dhe i krahason me kohë të pandryshueshme, që koha e
    përgjigjes të mos tregojë sa shifra të para ishin të sakta.
    """
    code = normalize_code(code)
    if code is None:
        return None
    key = _key(secret)
    current = step_of(now)
    found: int | None = None
    for step in range(current - window, current + window + 1):
        if hmac.compare_digest(hotp(key, step), code):
            found = step if found is None else max(found, step)
    return found


def normalize_code(code: str) -> str | None:
    """Kodi pa hapësira (aplikacionet i shfaqin si «123 456»), ose `None` nëse nuk janë gjashtë shifra ASCII."""
    cleaned = code.replace(" ", "")
    if len(cleaned) == DIGITS and cleaned.isascii() and cleaned.isdigit():
        return cleaned
    return None


def otpauth_uri(secret: str, account: str, issuer: str) -> str:
    """URI që aplikacionet e vërtetimit e lexojnë (formati i Google Authenticator «Key URI»)."""
    label = quote(f"{issuer}:{account}", safe="")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer, safe='')}"
        f"&algorithm=SHA1&digits={DIGITS}&period={PERIOD}"
    )


def new_recovery_code() -> str:
    raw = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(_RECOVERY_LENGTH))
    return f"{raw[:5]}-{raw[5:]}"


def normalize_recovery_code(code: str) -> str | None:
    """Kodi i rimëkëmbjes pa vizë, hapësira dhe shkronja të mëdha, ose `None` nëse nuk ka formën e duhur."""
    cleaned = code.replace("-", "").replace(" ", "").lower()
    if len(cleaned) == _RECOVERY_LENGTH and all(c in _RECOVERY_ALPHABET for c in cleaned):
        return cleaned
    return None
