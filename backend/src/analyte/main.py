"""
Fabrika e aplikacionit FastAPI.

    uvicorn analyte.main:app --reload

`create_app` merr konfigurimin dhe, opsionalisht, shërbimet dhe mënyrën e
nisjes së punëve. Testet i japin të dyja — SQLite dhe `InlineRunner` — që
e gjithë rruga nga ngarkimi te shpjegimi të ekzekutohet brenda një kërkese,
pa Redis dhe pa PostgreSQL.

Pikat e administrimit të vlerësimit (§5) nuk janë këtu: eksperimentet
ekzekutohen nga harness-i në linjë komande, ku prejardhja e tyre — fara,
versioni i korpusit, git sha — regjistrohet pa ndërmjetës.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analyte.config import Settings, get_settings
from analyte.mail import Mailer, build_mailer
from analyte.orchestration.tasks import (
    ArqRunner,
    InlineRunner,
    JobRunner,
    Services,
    build_services,
)

from .api import (
    advice,
    auth,
    chat,
    documents,
    explanations,
    findings,
    privacy,
    problems,
    terminology,
    two_factor,
)
from .api.headers import SecurityHeaders


def create_app(
    settings: Settings | None = None,
    services: Services | None = None,
    runner: JobRunner | None = None,
    mailer: Mailer | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    services = services or build_services(settings)
    if runner is None:
        runner = (
            InlineRunner(services)
            if settings.job_runner == "inline"
            else ArqRunner(settings.redis_url)
        )

    app = FastAPI(
        title="ANALYTE",
        version="0.1.0",
        description="Bazimi determinist dhe verifikimi i shpjegimeve të analizave laboratorike.",
    )
    app.state.settings = settings
    app.state.sessions = services.sessions
    app.state.store = services.store
    app.state.runner = runner
    # Pa ndërtuar mailer nga konfigurimi, shërbimi nuk nis: regjistrimi pa email do të dështonte në heshtje.
    app.state.mailer = mailer or build_mailer(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    # Shtohet pas CORS, prandaj është më e jashtmja: kokat e sigurisë dalin edhe te përgjigjet e CORS (ADR 0018).
    app.add_middleware(SecurityHeaders)
    problems.install(app)
    for module in (auth, two_factor, documents, findings, explanations, terminology, advice, chat, privacy):
        app.include_router(module.router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def __getattr__(name: str):
    """`analyte.main:app` për uvicorn, i ndërtuar vetëm kur kërkohet — importi
    i modulit nga testet nuk duhet të kërkojë konfigurim prodhimi."""
    if name == "app":
        return create_app()
    raise AttributeError(name)
