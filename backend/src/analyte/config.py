"""
Konfigurimi i shërbimit, nga mjedisi ose nga `.env`.

"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
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
    ipv6_prefix_bits: int = 64
    """Adresat IPv6 numërohen sipas këtij prefiksi, jo adresë më adresë: një sulmues me një bllok
    /64 ndryshon adresën lirisht, dhe pa këtë çdo adresë do t'i hapte kovat e IP-së nga e para
    (ADR 0014). Adresat IPv4 numërohen të plota."""
    trusted_proxy_hops: int = 0
    """Sa ndërmjetës të besuar qëndrojnë para shërbimit. 0 = adresa e lidhjes;
    n > 0 = e n-ta nga e djathta te `X-Forwarded-For`. Mos e rrit pa proxy:
    koka mund ta shkruajë kushdo."""

    mail_backend: Literal["smtp", "console"] = "smtp"
    """`smtp` dërgon me SMTP (në zhvillim, kutia e provës e Mailtrap). `console` shkruan mesazhin te log-u
    dhe është vetëm për zhvillim pa SMTP: log-u mban adresën dhe lidhjen e konfirmimit (ADR 0016)."""
    smtp_host: str = ""
    """P.sh. `sandbox.smtp.mailtrap.io`. Bosh me `smtp` = shërbimi nuk nis (nuk ka email në heshtje)."""
    smtp_port: int = 587
    smtp_security: Literal["starttls", "ssl", "none"] = "starttls"
    smtp_username: str = ""
    smtp_password: SecretStr | None = None
    mail_from: str = "ANALYTE <noreply@analyte.local>"
    frontend_url: str = "http://localhost:3000"
    """Baza e lidhjeve në email: `{frontend_url}/confirm?token=…`."""
    confirm_token_hours: int = 24
    """Sa vlen lidhja e konfirmimit. Përdoret një herë."""
    register_window_minutes: int = 60
    register_max_per_ip: int = 10
    """Kërkesa regjistrimi ose ridërgimi nga një IP brenda dritares: kufizon sa email-e mund të nisë
    një vend. Numërohen të gjitha kërkesat, jo vetëm ato me email të ri, që kufizimi të mos tregojë
    nëse një email ka llogari."""
    register_max_per_email: int = 3
    """Kërkesa për një email nga çdo IP brenda dritares: kufizon sa mesazhe merr një adresë."""

    reset_token_minutes: int = 60
    """Sa vlen lidhja e rivendosjes së fjalëkalimit. Më e shkurtër se ajo e konfirmimit: një lidhje e tillë hap
    llogarinë, jo vetëm e aktivizon (ADR 0018). Përdoret një herë."""
    reset_submit_max_per_ip: int = 20
    """Dorëzime të formës së rivendosjes nga një IP brenda `register_window_minutes`, të suksesshme ose jo."""

    mfa_challenge_minutes: int = 5
    """Sa vlen sfida e dhënë pas fjalëkalimit të saktë, që hapi i dytë i hyrjes të mbarojë (ADR 0018)."""
    mfa_max_failures_pair: int = 5
    """Kode të gabuara për një çift (përdorues, IP) brenda `login_window_minutes`."""
    mfa_max_failures_ip: int = 20
    mfa_max_failures_user: int = 10
    """Kode të gabuara për një përdorues nga çdo IP. Më i ulët se kufiri i fjalëkalimit: hapësira e një kodi me gjashtë
    shifra është vetëm një milion, dhe kodi kontrollohet vetëm pasi fjalëkalimi është i saktë."""
    mfa_recovery_codes: int = 8
    mfa_issuer: str = "ANALYTE"
    """Emri që shfaq aplikacioni i vërtetimit pranë kodit."""

    mail_send_attempts: int = 3
    """Sa herë provohet dërgimi i një mesazhi para se të lihet si i padërguar (ADR 0018)."""
    mail_retry_backoff_seconds: float = 2.0
    """Pritja para provës së dytë; dyfishohet me secilën tjetër."""
    mail_resend_after_minutes: int = 10
    """Një mesazh i padërguar merret nga kalimi periodik vetëm pasi ka kaluar kjo kohë: dërgimi në sfond ka mbaruar deri atëherë."""
    mail_auto_reissue_per_day: int = 2
    """Sa lidhje të reja mund të nxjerrë kalimi periodik automatikisht për një përdorues në 24 orë: kufi që ai të mos
    përdoret për të mbushur një kuti postare."""
    mail_delivery_retention_days: int = 30
    """Sa mbahen regjistrimet e dërgimit (pa adresa); pastaj fshihen nga kalimi periodik."""

    job_runner: Literal["inline", "arq"] = "arq"
    """`inline` e përpunon dokumentin brenda kërkesës — vetëm për teste dhe
    prova; `arq` e dërgon te radha dhe kërkesa kthehet menjëherë (NFR4)."""

    ocr: bool = True
    """Lexo dokumentet e skanuara me Tesseract kur motori gjendet."""

    cors_origins: list[str] = ["http://localhost:3000"]

    document_retention_days: int = Field(default=0, ge=0)
    """Sa ditë ruhet një dokument pas ngarkimit (ADR 0019). 0 = ruhet derisa pronari ta fshijë (e fikur, parazgjedhja).
    Me një vlerë më të madhe, punëtori fshin çdo orë dokumentet më të vjetra, me të njëjtën rrugë si fshirja nga
    pronari: skedari i koduar, gjetjet, shpjegimet. Vendimi për afatin është i autorit, jo i kodit."""

    service_generator: Literal["template", "model"] = "template"
    """Ç'gjeneron shpjegimet te aplikacioni i uebit (ADR 0017). `template` (parazgjedhja) nuk dërgon asnjë të dhënë jashtë
    sistemit. `model` i dërgon ofruesit konteksti i strukturuar i çdo dokumenti, dhe kërkon `llm_provider`, `llm_model` dhe
    `llm_api_key`. E ndarë nga `llm_provider` me qëllim: ofruesi duhet te `.env` edhe për eksperimentet (harness-i), dhe
    kushdo që i ekzekuton ato nuk duhet t'u dërgojë ngarkimet e vërteta një ofruesi pa e vendosur këtë shprehimisht."""
    llm_provider: str = ""
    """`gemini`, `mistral`, `groq`, `cerebras`, `openrouter` ose `openai_compatible` (me
    `llm_base_url`). Bosh = pa model: gjeneruesi është shablloni."""
    llm_base_url: str = ""
    llm_model: str = ""
    """Emri i saktë i modelit, i fiksuar (jo `-preview`): një rezultat nuk
    atribuohet dot te një model që ndryshon pa dije."""
    llm_api_key: SecretStr | None = None
    llm_judge_model: str = ""
    """Modeli i gjykatësit të E12. Bosh = përdoret `llm_model`, çka e bën
    modelin gjykatës të daljes së vet; kufizimi duhet raportuar."""
    llm_judge_provider: str = ""
    llm_judge_api_key: SecretStr | None = None
    llm_judge_base_url: str = ""
    """Gjykatësi mund të jetë ofrues tjetër; bosh = i njëjti me gjeneruesin."""
    llm_temperature: float = 0.0
    llm_thinking: str = "low"
    """Niveli i arsyetimit të brendshëm (`thinkingLevel`); bosh = parazgjedhja e ofruesit."""
    llm_requests_per_minute: int = 10
    llm_max_output_tokens: int = 4096
    llm_timeout_seconds: int = 120


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
