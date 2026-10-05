"""
Hapi i dytë i hyrjes me kod të kohës (TOTP) dhe kode rimëkëmbjeje (ADR 0018).

**Regjistrimi** (përdorues i hyrë): `enroll` nxjerr një sekret të ri dhe e kthen një herë, `confirm` e aktivizon kur
përdoruesi dërgon një kod të vlefshëm dhe kthen kodet e rimëkëmbjes (një herë). Sekreti ruhet i koduar me të njëjtin
çelës Fernet si skedarët; kodet e rimëkëmbjes vetëm si HMAC me çelës.

**Hyrja.** Me hap të dytë, fjalëkalimi i saktë nuk jep tokenë por një sfidë të shkurtër (te `auth.login`); `login/verify`
e shkëmben sfidën dhe një kod me seancën. Rregullat:

  - kodet e gabuara kufizohen para se kodi të kontrollohet, sipas përdoruesit dhe çiftit (përdorues, IP) dhe IP-së;
  - një hap kohe i pranuar nuk pranohet dy herë (`totp_last_step`, e shkruar me UPDATE të kushtëzuar);
  - një kod rimëkëmbjes vlen një herë (UPDATE i kushtëzuar mbi `used_at`);
  - sfida lidhet me fjalëkalimin dhe me gjendjen e hapit të dytë: pas rivendosjes së fjalëkalimit ose çaktivizimit
    pushon;
  - një sfidë e pavlefshme, e skaduar ose e vjetruar kthen të njëjtën 401 si një kod i gabuar.

**Gabimet e një përdoruesi të hyrë** janë 400, jo 401: klienti e merr 401-ën si seancë të humbur dhe provon rifreskim.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from analyte import twofactor
from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import RecoveryCodeRow, UserRow
from analyte.security import (
    TokenError,
    credential_binding,
    keyed_hash,
    read_challenge,
    verify_password,
)

from . import auth_sessions, deps, throttle
from .problems import Problem
from .schemas import (
    CodeIn,
    DisableTwoFactorIn,
    LoginVerifyIn,
    RecoveryCodes,
    Tokens,
    TwoFactorEnrollment,
    TwoFactorStatus,
)

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("analyte.api")


def _recovery_key(config: Settings, user: UserRow, normalized: str) -> str:
    return keyed_hash(config.jwt_secret, "recovery-code", f"{user.id}\0{normalized}")


def _remaining(db: Session, user_id: object) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(RecoveryCodeRow)
            .where(RecoveryCodeRow.user_id == user_id, RecoveryCodeRow.used_at.is_(None))
        )
        or 0
    )


def _consume(
    db: Session,
    store: EncryptedStore,
    config: Settings,
    user: UserRow,
    code: str,
    now: datetime,
    *,
    recovery: bool,
) -> tuple[str, int | None] | None:
    """Shpenzon një kod: `("totp", hapi)` ose `("recovery", None)`, ose `None` nëse nuk vlen.

    Shpenzimi është gjithmonë një UPDATE i kushtëzuar, jo lexim-pastaj-shkrim: dy kërkesa me të njëjtin kod nuk e
    fitojnë të dyja, edhe në PostgreSQL me transaksione paralele.
    """
    digits = twofactor.normalize_code(code)
    if digits is not None:
        if user.totp_secret_encrypted is None:
            return None
        try:
            secret = store.decrypt_text(user.totp_secret_encrypted)
        except InvalidToken:
            # Çelësi i kodimit ndryshoi: asnjë kod nuk mund të kontrollohet. Duhet të duket te log-u, jo të kalojë në heshtje.
            log.error("sekreti TOTP nuk dekodohet: çelësi i ruajtjes ka ndryshuar")
            return None
        step = twofactor.match(secret, digits, now.timestamp())
        if step is None:
            return None
        spent = db.execute(
            update(UserRow)
            .where(
                UserRow.id == user.id,
                or_(UserRow.totp_last_step.is_(None), UserRow.totp_last_step < step),
            )
            .values(totp_last_step=step)
        ).rowcount
        return ("totp", step) if spent == 1 else None
    if recovery:
        normalized = twofactor.normalize_recovery_code(code)
        if normalized is None:
            return None
        spent = db.execute(
            update(RecoveryCodeRow)
            .where(
                RecoveryCodeRow.user_id == user.id,
                RecoveryCodeRow.code_key == _recovery_key(config, user, normalized),
                RecoveryCodeRow.used_at.is_(None),
            )
            .values(used_at=now)
        ).rowcount
        return ("recovery", None) if spent == 1 else None
    return None


def _ip(request: Request, config: Settings) -> str:
    return throttle.client_ip(request, config.trusted_proxy_hops, config.ipv6_prefix_bits)


@router.get("/2fa", response_model=TwoFactorStatus)
def status(
    user: UserRow = Depends(deps.current_user),
    db: Session = Depends(deps.session),
) -> TwoFactorStatus:
    enabled = user.totp_enabled_at is not None
    return TwoFactorStatus(enabled=enabled, recovery_codes_remaining=_remaining(db, user.id) if enabled else 0)


@router.post("/2fa/enroll", response_model=TwoFactorEnrollment)
def enroll(
    user: UserRow = Depends(deps.current_user),
    store: EncryptedStore = Depends(deps.store),
    config: Settings = Depends(deps.settings),
) -> TwoFactorEnrollment:
    """Nis regjistrimin: një sekret i ri, i dukshëm vetëm në këtë përgjigje. Thirrja e dytë para konfirmimit e
    zëvendëson sekretin; pasi hapi i dytë aktivizohet, kjo pikë kthen 409 dhe sekreti nuk lexohet më."""
    if user.totp_enabled_at is not None:
        raise Problem(409, "Hapi i dytë është tashmë aktiv", "Çaktivizojeni para se ta regjistroni sërish.")
    secret = twofactor.new_secret()
    user.totp_secret_encrypted = store.encrypt_text(secret)
    user.totp_last_step = None
    return TwoFactorEnrollment(
        secret=secret, otpauth_uri=twofactor.otpauth_uri(secret, user.email, config.mfa_issuer)
    )


@router.post("/2fa/confirm", response_model=RecoveryCodes)
def confirm(
    body: CodeIn,
    request: Request,
    current: deps.Login = Depends(deps.current_login),
    db: Session = Depends(deps.session),
    store: EncryptedStore = Depends(deps.store),
    config: Settings = Depends(deps.settings),
) -> RecoveryCodes:
    """Aktivizon hapin e dytë me kodin e parë të vlefshëm dhe kthen kodet e rimëkëmbjes, një herë."""
    user, now = current.user, datetime.now(UTC)
    if user.totp_enabled_at is not None:
        raise Problem(409, "Hapi i dytë është tashmë aktiv")
    if user.totp_secret_encrypted is None:
        raise Problem(409, "Regjistrimi nuk ka nisur", "Kërkoni fillimisht një sekret të ri.")
    keys = throttle.mfa_keys(user.id, _ip(request, config), config)
    throttle.check_mfa(db, config, keys, now)
    if _consume(db, store, config, user, body.code, now, recovery=False) is None:
        throttle.record_mfa_failure(db, config, keys, now)
        raise Problem(400, "Kodi është i pavlefshëm", "Kontrolloni orën e telefonit dhe provoni kodin e radhës.")

    user.totp_enabled_at = now
    codes = [twofactor.new_recovery_code() for _ in range(config.mfa_recovery_codes)]
    db.execute(delete(RecoveryCodeRow).where(RecoveryCodeRow.user_id == user.id))
    for code in codes:
        normalized = twofactor.normalize_recovery_code(code)
        assert normalized is not None
        db.add(
            RecoveryCodeRow(user_id=user.id, code_key=_recovery_key(config, user, normalized), created_at=now)
        )
    throttle.clear_pair(db, keys)
    auth_sessions.revoke_others(db, user.id, current.auth_session.id, "two_factor_enabled", now)
    audit.two_factor_enabled(db, user.id)
    return RecoveryCodes(recovery_codes=codes)


@router.post("/2fa/disable", status_code=204)
def disable(
    body: DisableTwoFactorIn,
    request: Request,
    user: UserRow = Depends(deps.current_user),
    db: Session = Depends(deps.session),
    store: EncryptedStore = Depends(deps.store),
    config: Settings = Depends(deps.settings),
) -> Response:
    """Çaktivizon hapin e dytë. Kërkon fjalëkalimin e tanishëm dhe një kod (aplikacioni ose rimëkëmbjeje): një token
    aksesi i vjedhur vetëm nuk mjafton. Gabimet kufizohen si te hyrja."""
    now = datetime.now(UTC)
    if user.totp_enabled_at is None:
        raise Problem(409, "Hapi i dytë nuk është aktiv")
    keys = throttle.mfa_keys(user.id, _ip(request, config), config)
    throttle.check_mfa(db, config, keys, now)
    invalid = Problem(400, "Fjalëkalimi ose kodi është i gabuar")
    # Fjalëkalimi para kodit: një fjalëkalim i gabuar nuk duhet të shpenzojë një kod rimëkëmbjes të saktë.
    if not verify_password(user.password_hash, body.password):
        throttle.record_mfa_failure(db, config, keys, now)
        raise invalid
    if _consume(db, store, config, user, body.code, now, recovery=True) is None:
        throttle.record_mfa_failure(db, config, keys, now)
        raise invalid

    user.totp_secret_encrypted = None
    user.totp_enabled_at = None
    user.totp_last_step = None
    db.execute(delete(RecoveryCodeRow).where(RecoveryCodeRow.user_id == user.id))
    throttle.clear_pair(db, keys)
    audit.two_factor_disabled(db, user.id)
    return Response(status_code=204)


@router.post("/login/verify", response_model=Tokens)
def verify_login(
    body: LoginVerifyIn,
    request: Request,
    db: Session = Depends(deps.session),
    store: EncryptedStore = Depends(deps.store),
    config: Settings = Depends(deps.settings),
) -> Tokens:
    """Hapi i dytë i hyrjes: sfida nga `login` dhe një kod. Hap seancën kur kodi vlen."""
    now = datetime.now(UTC)
    invalid = Problem(401, "Sfida ose kodi është i pavlefshëm")
    try:
        user_id, binding = read_challenge(body.challenge, config.jwt_secret)
    except TokenError:
        raise invalid from None

    # Kufizimi para çdo kontrolli të kodit. `user_id` vjen nga një sfidë e nënshkruar, jo nga klienti.
    keys = throttle.mfa_keys(user_id, _ip(request, config), config)
    throttle.check_mfa(db, config, keys, now)

    user = db.get(UserRow, user_id)
    if (
        user is None
        or user.totp_enabled_at is None
        or user.email_confirmed_at is None
        or binding
        != credential_binding(config.jwt_secret, user.id, user.password_hash, user.totp_enabled_at)
    ):
        # Fjalëkalimi ndryshoi ose hapi i dytë u çaktivizua pas sfidës: pa kontrolluar asnjë kod.
        raise invalid

    spent = _consume(db, store, config, user, body.code, now, recovery=True)
    if spent is None:
        throttle.record_mfa_failure(db, config, keys, now)
        raise invalid
    if spent[0] == "recovery":
        audit.recovery_code_used(db, user.id, _remaining(db, user.id))
    throttle.clear_pair(db, keys)
    return auth_sessions.open_session(db, user, config, now)
