"""
Mbrojtja e të dhënave mbi PostgreSQL të vërtetë (ADR 0019).

    make test-postgres

"""

from __future__ import annotations

import os
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import func, select

from analyte import erasure
from analyte.generation.templates import TemplateGenerator
from analyte.persistence.tables import AuditEventRow, DocumentRow, UserRow
from tests.integration.test_data_protection import (
    FILENAME,
    FakeClient,
    World,
    _erase,
    _pdf,
)

URL = os.environ.get("ANALYTE_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(URL is None, reason="ANALYTE_TEST_DATABASE_URL mungon")

BACKEND = Path(__file__).resolve().parents[2] / "backend"


@pytest.fixture
def database(monkeypatch):
    """Bazë e re nga migrimet për çdo test."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    admin_url, _, name = URL.rpartition("/")
    admin = create_engine(f"{admin_url}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()

    monkeypatch.setenv("ANALYTE_DATABASE_URL", URL)
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "head")
    return URL


@pytest.fixture(scope="module")
def pdfs():
    return {
        "a": _pdf("pg-a"),
        "named": _pdf(
            "pg-named",
            "Dr. Arben Krasniqi vëren anemi të lehtë. Rekomandohet kontroll pas tre muajsh.",
        ),
    }


def test_consent_and_the_gate_on_postgres(tmp_path, database, pdfs):
    from analyte.generation.llm import LlmGenerator

    fake = FakeClient()
    world = World(tmp_path, LlmGenerator(fake), database_url=database, service_generator="model")
    headers = world.user("pg-pelqim@shembull.al")

    declined = world.upload(headers, pdfs["a"])  # pa pëlqim
    named = world.upload(headers, pdfs["named"], consent=True)  # me pëlqim, por emër te citimi

    assert fake.prompts == []
    codes_declined = [n["code"] for n in world.explanation(headers, declined)["notices"]]
    codes_named = [n["code"] for n in world.explanation(headers, named)["notices"]]
    assert "model_declined" in codes_declined and "model_withheld" in codes_named
    assert world.document_row(declined).model_use == "no_consent"
    assert world.document_row(named).model_use == "identifying_content"
    assert world.document_row(named).model_consent_at is not None


def test_erasure_cascades_on_postgres_and_leaves_the_other_user_alone(tmp_path, database, pdfs):
    world = World(tmp_path, TemplateGenerator(), database_url=database)
    bob = world.user("pg-bob@shembull.al")
    bob_doc = world.upload(bob, pdfs["a"])
    bob_counts, bob_files = world.counts(), world.stored_files()

    alice = world.user("pg-alice@shembull.al")
    one, two = world.upload(alice, pdfs["a"]), world.upload(alice, pdfs["a"])
    assert world.client.delete(f"/documents/{one}", headers=alice).status_code == 204
    assert world.client.delete(f"/documents/{one}", headers=alice).status_code == 404
    assert _erase(world, alice, "gabim-gabim-gabim").status_code == 403
    assert _erase(world, alice).status_code == 204

    assert world.counts() == bob_counts and world.stored_files() == bob_files
    assert world.client.get(f"/documents/{bob_doc}/explanation", headers=bob).status_code == 200
    with world.services.sessions() as session:
        assert session.scalar(select(func.count()).select_from(UserRow)) == 1
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEventRow)
                .where(AuditEventRow.user_id.is_(None))
            )
            >= 3
        )
        assert session.get(DocumentRow, UUID(two)) is None


def test_two_simultaneous_erasures_of_the_same_account_both_succeed_and_leave_nothing(
    tmp_path, database, pdfs
):
    world = World(tmp_path, TemplateGenerator(), database_url=database)
    headers = world.user("pg-gare@shembull.al")
    for _ in range(3):
        world.upload(headers, pdfs["a"])
    with world.services.sessions() as session:
        user_id = session.scalar(select(UserRow.id).where(UserRow.email == "pg-gare@shembull.al"))

    barrier, errors, erased = threading.Barrier(2), [], []

    def erase() -> None:
        try:
            with world.services.sessions() as session:
                user = session.get(UserRow, user_id)
                # të dyja e kanë ngarkuar përdoruesin para se ndonjëra të fshijë
                barrier.wait(timeout=10)
                erased.append(
                    erasure.erase_user(session, world.services.store, user, world.settings)
                )
                session.commit()
        except Exception as error:  # noqa: BLE001
            errors.append(error)

    threads = [threading.Thread(target=erase) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert errors == [] and len(erased) == 2
    assert set(world.counts().values()) == {0} and world.stored_files() == set()
    with world.services.sessions() as session:
        assert session.scalar(select(func.count()).select_from(UserRow)) == 0


def test_two_simultaneous_deletions_of_one_document_leave_one_204_and_no_error(
    tmp_path, database, pdfs
):
    world = World(tmp_path, TemplateGenerator(), database_url=database)
    headers = world.user("pg-dyfish@shembull.al")
    document_id = world.upload(headers, pdfs["a"])

    statuses: list[int] = []
    barrier = threading.Barrier(2)

    def delete() -> None:
        barrier.wait(timeout=10)
        statuses.append(
            world.client.delete(f"/documents/{document_id}", headers=headers).status_code
        )

    threads = [threading.Thread(target=delete) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(statuses) in ([204, 204], [204, 404]), statuses  # kurrë 500
    assert set(world.counts().values()) == {0} and world.stored_files() == set()


def test_retention_on_postgres(tmp_path, database, pdfs):
    world = World(tmp_path, TemplateGenerator(), database_url=database)
    headers = world.user("pg-afat@shembull.al")
    old, fresh = world.upload(headers, pdfs["a"]), world.upload(headers, pdfs["a"])
    now = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
    with world.services.sessions() as session:
        session.get(DocumentRow, UUID(old)).uploaded_at = now - timedelta(days=40)
        session.get(DocumentRow, UUID(fresh)).uploaded_at = now - timedelta(days=5)
        session.commit()

    result = erasure.purge_expired(
        world.services.sessions, world.services.store, now=now, retention_days=30
    )
    assert (result.purged, result.failed) == (1, 0)
    with world.services.sessions() as session:
        assert [d for d in session.scalars(select(DocumentRow.id))] == [UUID(fresh)]
    assert len(world.stored_files()) == 1
    assert [e.payload for e in world.audit("document.expired")] == [{"retention_days": 30}]


def test_export_on_postgres(tmp_path, database, pdfs):
    world = World(tmp_path, TemplateGenerator(), database_url=database)
    headers = world.user("pg-eksport@shembull.al")
    document_id = world.upload(headers, pdfs["a"])
    data = world.client.get("/me/export", headers=headers).json()
    assert [d["id"] for d in data["documents"]] == [document_id]
    assert data["documents"][0]["filename"] == FILENAME and data["documents"][0]["findings"]
