"""
Punëtori i radhës (arq).

    arq analyte.orchestration.worker.WorkerSettings

"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from arq import cron
from arq.connections import RedisSettings

from analyte import outbox
from analyte.config import get_settings
from analyte.erasure import purge_expired
from analyte.mail import MailConfigError, build_mailer

from .tasks import build_services, run_document

log = logging.getLogger("analyte.worker")


async def startup(ctx: dict) -> None:
    settings = get_settings()
    ctx["services"] = build_services(settings)
    try:
        ctx["mailer"] = build_mailer(settings)
    except MailConfigError:
        ctx["mailer"] = None
        log.warning("posta nuk është konfiguruar: rindërgimi i mesazheve çaktivizohet")


async def run_document_job(ctx: dict, document_id: str) -> None:
    await asyncio.to_thread(run_document, ctx["services"], UUID(document_id))


async def resend_unsent_job(ctx: dict) -> None:
    mailer = ctx.get("mailer")
    if mailer is None:
        return
    report = await asyncio.to_thread(
        outbox.resend_unsent, ctx["services"].sessions, mailer, get_settings()
    )
    if report.examined:
        log.info(
            "rindërgimi: %d të shqyrtuara, %d të rilëshuara, %d të dërguara, %d dështime, %d të skaduara, %d të kaluara",
            report.examined,
            report.reissued,
            report.sent,
            report.failed,
            report.expired,
            report.skipped,
        )


async def purge_expired_job(ctx: dict) -> None:
    services = ctx["services"]
    await asyncio.to_thread(
        purge_expired,
        services.sessions,
        services.store,
        now=datetime.now(UTC),
        retention_days=get_settings().document_retention_days,
    )


class WorkerSettings:
    functions = [run_document_job]
    cron_jobs = [
        cron(resend_unsent_job, minute=set(range(0, 60, 10)), run_at_startup=False),
        cron(purge_expired_job, minute={7}),
    ]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 4
    job_timeout = 600
