"""
Punëtori i radhës (arq).

    arq analyte.orchestration.worker.WorkerSettings

Puna vetë është sinkrone — PyMuPDF, Tesseract, rregullat — prandaj
ekzekutohet në një fije më vete, që cikli asinkron i arq-së të mbetet i
lirë për punët e tjera.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from arq.connections import RedisSettings

from analyte.config import get_settings

from .tasks import build_services, run_document


async def startup(ctx: dict) -> None:
    ctx["services"] = build_services(get_settings())


async def run_document_job(ctx: dict, document_id: str) -> None:
    await asyncio.to_thread(run_document, ctx["services"], UUID(document_id))


class WorkerSettings:
    functions = [run_document_job]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 4
    job_timeout = 600
