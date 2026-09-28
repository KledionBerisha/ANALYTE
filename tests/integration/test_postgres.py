"""
E njëjta rrugë mbi PostgreSQL të vërtetë.

    make test-postgres

Anashkalohet kur `ANALYTE_TEST_DATABASE_URL` mungon, që testet e zakonshme
të mos kërkojnë Docker. Kur ekziston, baza e testit fshihet dhe ndërtohet
nga migrimet — jo nga modelet — që të provohet skema që sheh prodhimi,
dhe një dokument çohet nga ngarkimi te shpjegimi.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

URL = os.environ.get("ANALYTE_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(URL is None, reason="ANALYTE_TEST_DATABASE_URL mungon")

BACKEND = Path(__file__).resolve().parents[2] / "backend"


@pytest.fixture(scope="module")
def client(tmp_path_factory, monkeypatch_module):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    from analyte.config import Settings
    from analyte.generation.templates import TemplateGenerator
    from analyte.main import create_app
    from analyte.orchestration.tasks import InlineRunner, Services
    from analyte.persistence.database import make_engine, make_session_factory
    from analyte.persistence.storage import EncryptedStore

    admin_url, _, database = URL.rpartition("/")
    admin = create_engine(f"{admin_url}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{database}"'))
    admin.dispose()

    monkeypatch_module.setenv("ANALYTE_DATABASE_URL", URL)
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "head")

    tmp = tmp_path_factory.mktemp("pg")
    settings = Settings(
        database_url=URL,
        jwt_secret="p" * 48,
        storage_key=Fernet.generate_key().decode(),
        storage_dir=tmp / "storage",
        job_runner="inline",
        ocr=False,
    )
    services = Services(
        sessions=make_session_factory(make_engine(URL)),
        store=EncryptedStore(settings.storage_dir, settings.storage_key),
        generator=TemplateGenerator(),
    )
    return TestClient(create_app(settings, services, InlineRunner(services)))


@pytest.fixture(scope="module")
def monkeypatch_module():
    patch = pytest.MonkeyPatch()
    yield patch
    patch.undo()


def test_upload_to_explanation_on_postgres(client):
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    rng = random.Random("postgres/0")
    document = build_document(rng, IdFactory(rng), scanned_share=0.0)
    pdf, truth = render(document, seed=5, index=0)

    password = "fjalekalim-postgres-testi"
    client.post("/auth/register", json={"email": "pg@shembull.al", "password": password})
    token = client.post("/auth/login", json={"email": "pg@shembull.al", "password": password}).json()
    headers = {"Authorization": f"Bearer {token['access_token']}"}

    uploaded = client.post(
        "/documents", headers=headers, files={"file": ("a.pdf", pdf, "application/pdf")}
    ).json()
    document_id = uploaded["id"]

    assert client.get(f"/documents/{document_id}/status", headers=headers).json()["state"] == "delivered"
    findings = client.get(f"/documents/{document_id}/findings", headers=headers).json()
    expected = {f.analyte_code: format(f.value_canonical, "f") for f in truth.context.findings}
    assert {f["analyte_code"]: f["value_canonical"] for f in findings} == expected
    explanation = client.get(f"/documents/{document_id}/explanation", headers=headers).json()
    assert explanation["verification"]["passed"] is True
