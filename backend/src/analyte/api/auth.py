"""
Regjistrimi, konfirmimi i email-it, hyrja dhe rifreskimi.

"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from analyte import mail, outbox
from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.persistence.tables import EmailConfirmationRow, PasswordResetRow, UserRow
from analyte.security import (
    TokenError,
    credential_binding,
    hash_password,
    issue_challenge,
    keyed_hash,
    read_token,
    verify_password,
)

from . import auth_sessions, deps, throttle
from .problems import Problem
from .schemas import (
    ConfirmIn,
    Credentials,
    EmailIn,
    MfaChallenge,
    RefreshIn,
    RegisterOut,
    ResetIn,
    Tokens,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_DECOY_HASH = hash_password("fjalëkalim-i-rremë-vetëm-për-kohën")
"""Kur email-i nuk ekziston, fjalëkalimi krahasohet me këtë. Pa të, hyrja
me email të panjohur do të ishte dukshëm më e shpejtë — Argon2 është i
ngadalshëm me qëllim — dhe koha do të tregonte atë që mesazhi e fsheh."""

REGISTER_REPLY = (
    "Nëse email-i mund të përdoret, ju dërguam një mesazh. Hapni lidhjen në të për të aktivizuar "
    "llogarinë; nëse nuk e shihni, kontrolloni dosjen e mesazheve të padëshiruara."
)
"""E njëjta për çdo email (ADR 0016)."""

RESET_REPLY = (
    "Nëse email-i ka llogari, ju dërguam një mesazh me lidhjen për të vendosur një fjalëkalim të ri. "
    "Nëse nuk e shihni, kontrolloni dosjen e mesazheve të padëshiruara."
)
"""E njëjta për çdo email, me llogari ose pa (ADR 0018)."""

_EMAIL = re.compile(r"^[^@\s<>,;:\"'()\[\]\\]+@[^@\s<>,;:\"'()\[\]\\]+\.[^@\s<>,;:\"'()\[\]\\]+$")


def _normalize(email: str) -> str:
    """Email i pastruar. Refuzon çdo hapësirë, kontroll ose shenjë që mund të ndërtojë një kokë tjetër
    mesazhi (`\\n`, `,`, `<`): adresa shkon te një SMTP, dhe një rresht i ri aty do të ishte injektim."""
    email = email.strip().lower()
    if not _EMAIL.fullmatch(email):
        raise Problem(422, "Email i pavlefshëm")
    return email


@router.post("/register", response_model=RegisterOut, status_code=202)
def register(
    body: Credentials,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> RegisterOut:
    email = _normalize(body.email)
    if len(body.password) < config.min_password_length:
        raise Problem(
            422, "Fjalëkalim shumë i shkurtër", f"të paktën {config.min_password_length} shenja"
        )
    now = datetime.now(UTC)
    keys = throttle.registration_keys(
        email,
        throttle.client_ip(request, config.trusted_proxy_hops, config.ipv6_prefix_bits),
        config,
    )
    throttle.check_registration(db, config, keys, now)
    throttle.record_registration(db, config, keys, now)

    # Argon2 shpenzohet në të tria rastet, që koha të mos tregojë cili ndodhi.
    password_hash = hash_password(body.password)
    user = db.scalars(select(UserRow).where(UserRow.email == email)).first()
    outgoing: outbox.Outgoing

    if user is None:
        user = UserRow(email=email, password_hash=password_hash)
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            # Dikush e krijoi në të njëjtin çast: njëlloj si një email ekzistues, pa mesazh të dytë.
            db.rollback()
            return RegisterOut(message=REGISTER_REPLY)
        audit.user_registered(db, user.id)
        outgoing = outbox.prepare_confirmation(db, user, config, now)
    elif user.email_confirmed_at is None:
        # Regjistrimi i fundit fiton: fjalëkalimi zëvendësohet, që dikush që regjistroi email-in e një
        # tjetri më parë të mos e mbajë fjalëkalimin e llogarisë kur ajo konfirmohet.
        user.password_hash = password_hash
        outgoing = outbox.prepare_confirmation(db, user, config, now)
    else:
        subject, body_text = mail.already_registered_message(
            f"{config.frontend_url.rstrip('/')}/login"
        )
        outgoing = outbox.Outgoing(email, subject, body_text)

    # Ruhet para dërgimit: mesazhi nuk duhet të mbërrijë përpara tokenit që e verifikon, dhe detyra në
    # sfond hap sesionin e vet, që nuk duhet të presë një shkrim të pambaruar të kësaj kërkese.
    db.commit()
    background.add_task(outbox.deliver, request.app, outgoing)
    return RegisterOut(message=REGISTER_REPLY)


@router.post("/resend-confirmation", response_model=RegisterOut, status_code=202)
def resend_confirmation(
    body: EmailIn,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> RegisterOut:
    """Një lidhje e re për një llogari të pakonfirmuar. Përgjigja është e njëjtë me atë të regjistrimit."""
    email = _normalize(body.email)
    now = datetime.now(UTC)
    keys = throttle.registration_keys(
        email,
        throttle.client_ip(request, config.trusted_proxy_hops, config.ipv6_prefix_bits),
        config,
    )
    throttle.check_registration(db, config, keys, now)
    throttle.record_registration(db, config, keys, now)

    # koha e njëjtë me regjistrimin, qoftë llogaria e pakonfirmuar apo jo
    hash_password("kohë-e-barabartë")
    user = db.scalars(select(UserRow).where(UserRow.email == email)).first()
    if user is not None and user.email_confirmed_at is None:
        outgoing = outbox.prepare_confirmation(db, user, config, now)
        db.commit()  # si te regjistrimi: tokeni ruhet para se të nisë mesazhi
        background.add_task(outbox.deliver, request.app, outgoing)
    return RegisterOut(message=REGISTER_REPLY)


@router.post("/forgot-password", response_model=RegisterOut, status_code=202)
def forgot_password(
    body: EmailIn,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> RegisterOut:
    """Kërkon lidhjen për të vendosur fjalëkalim të ri (ADR 0018). Përgjigja është e njëjtë për çdo email.

    Një llogari e konfirmuar merr lidhjen e rivendosjes. Një e pakonfirmuar merr lidhjen e konfirmimit, jo atë të
    rivendosjes: rivendosja nuk duhet të jetë rrugë anash konfirmimit. Një email pa llogari nuk merr asgjë.
    """
    email = _normalize(body.email)
    now = datetime.now(UTC)
    keys = throttle.reset_keys(
        email,
        throttle.client_ip(request, config.trusted_proxy_hops, config.ipv6_prefix_bits),
        config,
    )
    throttle.check_registration(db, config, keys, now)
    throttle.record_registration(db, config, keys, now)

    # koha e njëjtë, qoftë llogaria e konfirmuar, e pakonfirmuar apo e munguar
    hash_password("kohë-e-barabartë")
    user = db.scalars(select(UserRow).where(UserRow.email == email)).first()
    if user is not None:
        if user.email_confirmed_at is not None:
            outgoing = outbox.prepare_password_reset(db, user, config, now)
        else:
            outgoing = outbox.prepare_confirmation(db, user, config, now)
        db.commit()  # tokeni ruhet para se të nisë mesazhi
        background.add_task(outbox.deliver, request.app, outgoing)
    return RegisterOut(message=RESET_REPLY)


@router.post("/reset-password", status_code=204)
def reset_password(
    body: ResetIn,
    request: Request,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> Response:
    """Vendos fjalëkalimin e ri me tokenin e lidhjes (ADR 0018).

    Vlen një herë dhe skadon. Një token i panjohur, i përdorur ose i skaduar kthen të njëjtën gabim. Fjalëkalimi
    i ri hash-ohet para se tokeni të kontrollohet, që koha të mos tregojë nëse tokeni ishte i vlefshëm. Pas suksesit
    çdo seancë e përdoruesit revokohet; hapi i dytë, nëse ka, mbetet i paprekur (një kuti postare e vjedhur nuk
    e kalon).
    """
    now = datetime.now(UTC)
    keys = throttle.reset_submit_key(
        throttle.client_ip(request, config.trusted_proxy_hops, config.ipv6_prefix_bits), config
    )
    throttle.check_reset_submit(db, config, keys, now)
    throttle.record_registration(db, config, keys, now)
    if len(body.password) < config.min_password_length:
        raise Problem(
            422, "Fjalëkalim shumë i shkurtër", f"të paktën {config.min_password_length} shenja"
        )
    new_hash = hash_password(body.password)

    invalid = Problem(400, "Lidhja e rivendosjes është e pavlefshme ose ka skaduar")
    row = db.scalars(
        select(PasswordResetRow).where(
            PasswordResetRow.token_key
            == keyed_hash(config.jwt_secret, "password-reset", body.token)
        )
    ).first()
    if row is None or row.expires_at <= now:
        raise invalid
    user = db.get(UserRow, row.user_id)
    # Një llogari e pakonfirmuar nuk rivendoset: konfirmimi mbetet i vetmi rrugë për ta hapur (ADR 0018).
    if user is None or user.email_confirmed_at is None:
        raise invalid
    spent = db.execute(
        update(PasswordResetRow)
        .where(PasswordResetRow.id == row.id, PasswordResetRow.used_at.is_(None))
        .values(used_at=now)
    ).rowcount
    if spent == 0:
        raise invalid

    user.password_hash = new_hash
    db.execute(
        delete(PasswordResetRow).where(
            PasswordResetRow.user_id == user.id, PasswordResetRow.used_at.is_(None)
        )
    )
    auth_sessions.revoke_all(db, user.id, "password_reset", now)
    audit.password_reset(db, user.id)
    return Response(status_code=204)


@router.post("/confirm", status_code=204)
def confirm(
    body: ConfirmIn,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> Response:
    """Konfirmon email-in me tokenin e lidhjes. Vlen një herë; një token i panjohur, i përdorur ose i
    skaduar kthen të njëjtën gabim."""
    now = datetime.now(UTC)
    invalid = Problem(400, "Lidhja e konfirmimit është e pavlefshme ose ka skaduar")
    row = db.scalars(
        select(EmailConfirmationRow).where(
            EmailConfirmationRow.token_key
            == keyed_hash(config.jwt_secret, "email-confirm", body.token)
        )
    ).first()
    if row is None or row.expires_at <= now:
        raise invalid
    # Shpenzimi është një UPDATE i kushtëzuar, si te tokenët e rifreskimit: dy kërkesa me të njëjtën
    # lidhje nuk e fitojnë të dyja.
    spent = db.execute(
        update(EmailConfirmationRow)
        .where(EmailConfirmationRow.id == row.id, EmailConfirmationRow.used_at.is_(None))
        .values(used_at=now)
    ).rowcount
    if spent == 0:
        raise invalid
    user = db.get(UserRow, row.user_id)
    if user is not None and user.email_confirmed_at is None:
        user.email_confirmed_at = now
        audit.email_confirmed(db, user.id)
    return Response(status_code=204)


@router.post("/login", response_model=Tokens | MfaChallenge)
def login(
    body: Credentials,
    request: Request,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> Tokens | MfaChallenge:
    now = datetime.now(UTC)
    email = body.email.strip().lower()
    keys = throttle.keys_for(
        email,
        throttle.client_ip(request, config.trusted_proxy_hops, config.ipv6_prefix_bits),
        config,
    )
    # Kufizimi para fjalëkalimit: një çift i bllokuar refuzohet edhe me fjalëkalimin
    # e saktë, përndryshe provat do të vazhdonin derisa një të ketë sukses.
    throttle.check(db, config, keys, now)

    user = db.scalars(select(UserRow).where(UserRow.email == email)).first()
    stored = user.password_hash if user is not None else _DECOY_HASH
    if not verify_password(stored, body.password) or user is None:
        throttle.record_failure(db, config, keys, now)
        raise Problem(401, "Email ose fjalëkalim i gabuar")
    if user.email_confirmed_at is None:
        # Fjalëkalimi është i saktë, prandaj kjo përgjigje i thotë gjë vetëm atij që e di. Nuk numërohet si
        # dështim: përdoruesi nuk gabon, thjesht s'ka konfirmuar.
        raise Problem(
            403,
            "Email-i nuk është konfirmuar",
            "Hapni lidhjen që ju dërguam, ose kërkoni një të re.",
        )
    throttle.clear_pair(db, keys)
    if user.totp_enabled_at is not None:
        # Fjalëkalimi është i saktë: vetëm tani del një sfidë, që hapi i dytë të mos tregojë asgjë para saj (ADR 0018).
        binding = credential_binding(
            config.jwt_secret, user.id, user.password_hash, user.totp_enabled_at
        )
        return MfaChallenge(
            challenge=issue_challenge(
                user.id, binding, timedelta(minutes=config.mfa_challenge_minutes), config.jwt_secret
            )
        )
    return auth_sessions.open_session(db, user, config, now)


@router.post("/refresh", response_model=Tokens)
def refresh(
    body: RefreshIn,
    db: Session = Depends(deps.session),
    config: Settings = Depends(deps.settings),
) -> Tokens:
    try:
        claims = read_token(body.refresh_token, "refresh", config.jwt_secret)
    except TokenError:
        raise Problem(401, "Token rifreskimi i pavlefshëm ose i skaduar") from None
    return auth_sessions.rotate(db, claims, config, datetime.now(UTC))


@router.post("/logout", status_code=204)
def logout(
    current: deps.Login = Depends(deps.current_login),
    db: Session = Depends(deps.session),
) -> Response:
    """Revokon seancën: tokenët e aksesit dhe të rifreskimit pushojnë menjëherë."""
    auth_sessions.revoke(db, current.auth_session, "logout", datetime.now(UTC))
    return Response(status_code=204)


@router.post("/logout-all", status_code=204)
def logout_all(
    current: deps.Login = Depends(deps.current_login),
    db: Session = Depends(deps.session),
) -> Response:
    """Dil kudo: revokon çdo seancë të hapur të përdoruesit, edhe këtë, menjëherë."""
    auth_sessions.revoke_all(db, current.user.id, "logout_all", datetime.now(UTC))
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: UserRow = Depends(deps.current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, created_at=user.created_at)
