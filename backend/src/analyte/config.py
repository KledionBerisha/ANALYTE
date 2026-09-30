"""
Konfigurimi i shërbimit, nga mjedisi ose nga `.env`.

Dy vlera nuk kanë parazgjedhje me qëllim: sekreti i JWT-së dhe çelësi i
kodimit të skedarëve. Një shërbim që nis me vlera të njohura publikisht
do të dukej i sigurt pa qenë, prandaj pa to nuk nis fare. `.env.example`
tregon si gjenerohen.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANALYTE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://analyte:analyte@localhost:5433/analyte"
    redis_url: str = "redis://localhost:6379/0"
    storage_dir: Path = Path("storage")

    jwt_secret: str = Field(min_length=32)
    storage_key: str = Field(min_length=44)
    """Çelës Fernet: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`."""

    access_token_minutes: int = 30
    refresh_token_days: int = 7
    max_upload_mb: int = 20
    min_password_length: int = 10

    refresh_reuse_grace_seconds: int = 10
    """Një token rifreskimi i përdorur dy herë brenda kësaj kohe refuzohet pa
    revokuar seancën: dy kërkesa paralele të të njëjtit klient nuk janë vjedhje.
    Pas saj, ripërdorimi revokon seancën (ADR 0014)."""

    login_window_minutes: int = 15
    login_max_failures_pair: int = 5
    """Dështime për një çift (email, IP) brenda dritares."""
    login_max_failures_ip: int = 20
    """Dështime nga një IP, pavarësisht email-it — kundër provës së shumë llogarive."""
    login_max_failures_email: int = 20
    """Dështime për një email nga çdo IP — kundër provës së shpërndarë."""
    trusted_proxy_hops: int = 0
    """Sa ndërmjetës të besuar qëndrojnë para shërbimit. 0 = adresa e lidhjes;
    n > 0 = e n-ta nga e djathta te `X-Forwarded-For`. Mos e rrit pa proxy:
    koka mund ta shkruajë kushdo."""

    job_runner: Literal["inline", "arq"] = "arq"
    """`inline` e përpunon dokumentin brenda kërkesës — vetëm për teste dhe
    prova; `arq` e dërgon te radha dhe kërkesa kthehet menjëherë (NFR4)."""

    ocr: bool = True
    """Lexo dokumentet e skanuara me Tesseract kur motori gjendet."""

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
