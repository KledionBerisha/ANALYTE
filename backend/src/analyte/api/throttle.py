"""
Kufizimi i shpeshtësisë së hyrjeve (ADR 0014).

Tri kova numërojnë dështimet brenda një dritareje kohore, dhe një hyrje
refuzohet kur ndonjëra është e mbushur:

  - **çifti (email, IP)** — e ngushtë; ndalon ta provosh një llogari nga një vend;
  - **IP-ja** — më e gjerë; ndalon provën e shumë llogarive nga një vend;
  - **email-i** — më e gjerë; ndalon provën e shpërndarë të një llogarie nga shumë vende.

Çifti e mban kufirin e ngushtë pa e lënë dikë të mbyllë llogarinë e tjetrit:
dështimet e një sulmuesi nga një IP tjetër nuk e mbushin çiftin e viktimës.
Kova e email-it është kompromisi i ndërgjegjshëm, dhe ka kufi më të lartë.

**IPv6.** Një sulmues me një bllok /64 ndryshon adresën lirisht, prandaj adresat IPv6 numërohen sipas
prefiksit (parazgjedhja /64), jo adresë më adresë. Adresat IPv4, edhe ato të shkruara si IPv4-të-mapuara
në IPv6, numërohen të plota.

**Regjistrimi ka kovat e veta** (`check_registration`): çdo kërkesë regjistrimi ose ridërgimi nis një email,
dhe kufizimi i kufizon sa email-e mund të nisë një IP dhe sa merr një adresë. Numërohen të gjitha kërkesat,
jo vetëm ato me email të ri, kështu që përgjigjja «shumë kërkesa» nuk tregon nëse email-i ka llogari.

**Ajo që nuk bën.** Kufizimi vlen njësoj për email të panjohur dhe të
njohur: përgjigjja "shumë përpjekje" nuk tregon nëse llogaria ekziston, e
njëjta veti që ka mesazhi i hyrjes së dështuar. Dhe një hyrje e refuzuar nga
kufizimi nuk numërohet si dështim — përndryshe një sulmues do ta mbante një
llogari të mbyllur pafundësisht duke vazhduar të provojë.

Email-i dhe IP-ja ruhen vetëm si HMAC me çelës (`security.keyed_hash`).
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil

from fastapi import Request
from sqlalchemy import ColumnElement, delete, func, select
from sqlalchemy.orm import Session

from analyte.audit import logger as audit
from analyte.config import Settings
from analyte.persistence.tables import LoginFailureRow, RegistrationAttemptRow
from analyte.security import keyed_hash

from .problems import Problem


@dataclass(frozen=True, slots=True)
class Keys:
    """Identifikuesit e një përpjekjeje, tashmë të hash-uar."""

    email: str
    ip: str


def network_of(address: str, ipv6_prefix_bits: int = 64) -> str:
    """Identifikuesi i numërimit të një adrese: IPv4 e plotë; IPv6 e zvogëluar te prefiksi i saj.

    Një varg që nuk është adresë (p.sh. «panjohur») kthehet siç është.
    """
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return address
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        return str(ipaddress.ip_network(f"{ip}/{ipv6_prefix_bits}", strict=False))
    return str(ip)


def client_ip(request: Request, trusted_hops: int, ipv6_prefix_bits: int = 64) -> str:
    """Adresa e klientit.

    Pa ndërmjetës të besuar, adresa e lidhjes. Me `trusted_hops` = n, e n-ta
    nga e djathta te `X-Forwarded-For`: ndërmjetësit e besuar shtojnë në
    fund, prandaj çfarë shkruan klienti në fillim nuk numëron. Nëse koka
    është më e shkurtër se pritej, kthehet adresa e lidhjes — më mirë të
    kufizohet tepër sesa t'i besohet një koke që askush nuk e ka shkruar.
    """
    if trusted_hops > 0:
        hops = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",")]
        hops = [h for h in hops if h]
        if len(hops) >= trusted_hops:
            return network_of(hops[-trusted_hops], ipv6_prefix_bits)
    return network_of(request.client.host, ipv6_prefix_bits) if request.client else "panjohur"


def keys_for(email: str, ip: str, config: Settings) -> Keys:
    return Keys(
        email=keyed_hash(config.jwt_secret, "login-email", email),
        ip=keyed_hash(config.jwt_secret, "login-ip", ip),
    )


def _buckets(
    config: Settings, keys: Keys
) -> tuple[tuple[str, tuple[ColumnElement[bool], ...], int], ...]:
    by_email = LoginFailureRow.email_key == keys.email
    by_ip = LoginFailureRow.ip_key == keys.ip
    return (
        ("pair", (by_email, by_ip), config.login_max_failures_pair),
        ("ip", (by_ip,), config.login_max_failures_ip),
        ("email", (by_email,), config.login_max_failures_email),
    )


def check(db: Session, config: Settings, keys: Keys, now: datetime) -> None:
    """Hedh 429 nëse një kovë është e mbushur; përndryshe nuk bën asgjë."""
    window = timedelta(minutes=config.login_window_minutes)
    unlock: datetime | None = None
    for _, conditions, limit in _buckets(config, keys):
        recent = db.scalars(
            select(LoginFailureRow.at)
            .where(*conditions, LoginFailureRow.at >= now - window)
            .order_by(LoginFailureRow.at.desc())
            .limit(limit)
        ).all()
        if len(recent) >= limit:
            # Kova hapet kur dështimi i `limit`-it nga fundi del nga dritarja.
            free_at = recent[-1] + window
            unlock = free_at if unlock is None else max(unlock, free_at)
    if unlock is None:
        return
    seconds = max(1, ceil((unlock - now).total_seconds()))
    raise Problem(
        429,
        "Shumë përpjekje hyrjeje",
        f"Provoni sërish pas rreth {ceil(seconds / 60)} minutash.",
        headers={"Retry-After": str(seconds)},
    )


def record_failure(db: Session, config: Settings, keys: Keys, now: datetime) -> None:
    """Regjistron një dështim dhe e ruan menjëherë.

    Ruhet me `commit` këtu, jo nga sesioni i kërkesës: ai e kthen prapa çdo
    gjë kur kërkesa përfundon me përjashtim, dhe hyrja e dështuar përfundon
    me 401. Pa këtë, asnjë dështim nuk do të numërohej kurrë.
    """
    window = timedelta(minutes=config.login_window_minutes)
    db.execute(delete(LoginFailureRow).where(LoginFailureRow.at < now - window))
    db.add(LoginFailureRow(email_key=keys.email, ip_key=keys.ip, at=now))
    db.flush()
    for name, conditions, limit in _buckets(config, keys):
        count = db.scalar(
            select(func.count())
            .select_from(LoginFailureRow)
            .where(*conditions, LoginFailureRow.at >= now - window)
        )
        if count == limit:
            # Një herë për mbushje: kërkesat e refuzuara pas kësaj nuk shkruajnë
            # asgjë, prandaj log-u nuk mbushet nga një sulm që vazhdon.
            audit.login_throttled(db, name)
    db.commit()


def clear_pair(db: Session, keys: Keys) -> None:
    """Një hyrje e suksesshme i fshin dështimet e çiftit të vet, që një
    përdorues që gabon tri herë dhe pastaj hyn të mos mbetet afër kufirit.
    Dështimet e çifteve të tjera mbeten: një sulmues me llogarinë e vet nuk
    i rivendos numëruesit e IP-së ose të email-it të dikujt tjetër duke hyrë."""
    db.execute(
        delete(LoginFailureRow).where(
            LoginFailureRow.email_key == keys.email, LoginFailureRow.ip_key == keys.ip
        )
    )


# --------------------------------------------------------------------
# Regjistrimi dhe ridërgimi i konfirmimit (ADR 0016)
# --------------------------------------------------------------------


def registration_keys(email: str, ip: str, config: Settings) -> Keys:
    return Keys(
        email=keyed_hash(config.jwt_secret, "register-email", email),
        ip=keyed_hash(config.jwt_secret, "register-ip", ip),
    )


def _registration_buckets(
    config: Settings, keys: Keys
) -> tuple[tuple[ColumnElement[bool], int], ...]:
    return (
        (RegistrationAttemptRow.ip_key == keys.ip, config.register_max_per_ip),
        (RegistrationAttemptRow.email_key == keys.email, config.register_max_per_email),
    )


def check_registration(db: Session, config: Settings, keys: Keys, now: datetime) -> None:
    """Hedh 429 nëse një kovë regjistrimi është e mbushur. E njëjta përgjigje për email me llogari ose pa."""
    window = timedelta(minutes=config.register_window_minutes)
    unlock: datetime | None = None
    for condition, limit in _registration_buckets(config, keys):
        recent = db.scalars(
            select(RegistrationAttemptRow.at)
            .where(condition, RegistrationAttemptRow.at >= now - window)
            .order_by(RegistrationAttemptRow.at.desc())
            .limit(limit)
        ).all()
        if len(recent) >= limit:
            free_at = recent[-1] + window
            unlock = free_at if unlock is None else max(unlock, free_at)
    if unlock is None:
        return
    seconds = max(1, ceil((unlock - now).total_seconds()))
    raise Problem(
        429,
        "Shumë kërkesa",
        f"Provoni sërish pas rreth {ceil(seconds / 60)} minutash.",
        headers={"Retry-After": str(seconds)},
    )


def record_registration(db: Session, config: Settings, keys: Keys, now: datetime) -> None:
    """Regjistron kërkesën dhe e ruan menjëherë (si `record_failure`): ruajtja nuk duhet të humbasë nëse
    pjesa tjetër e kërkesës kthehet prapa."""
    window = timedelta(minutes=config.register_window_minutes)
    db.execute(delete(RegistrationAttemptRow).where(RegistrationAttemptRow.at < now - window))
    db.add(RegistrationAttemptRow(email_key=keys.email, ip_key=keys.ip, at=now))
    db.commit()
