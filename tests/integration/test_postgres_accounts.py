"""
Rivendosja, hapi i dytë dhe rindërgimi mbi PostgreSQL të vërtetë (ADR 0018).

    make test-postgres

"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

URL = os.environ.get("ANALYTE_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(URL is None, reason="ANALYTE_TEST_DATABASE_URL mungon")

BACKEND = Path(__file__).resolve().parents[2] / "backend"


@pytest.fixture
def world(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    from tests.fixtures.accounts import World

    admin_url, _, database = URL.rpartition("/")
    admin = create_engine(f"{admin_url}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{database}"'))
    admin.dispose()
    monkeypatch.setenv("ANALYTE_DATABASE_URL", URL)
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "head")

    w = World(tmp_path, database_url=URL)
    w.confirmed()
    return w


def test_a_reset_link_is_spent_by_exactly_one_of_many_parallel_requests(world):
    from tests.fixtures.accounts import EMAIL
    from tests.fixtures.mailbox import reset_token_in

    world.forgot()
    token = reset_token_in(world.outbox.to(EMAIL)[-1])
    with ThreadPoolExecutor(8) as pool:
        statuses = sorted(
            r.status_code
            for r in pool.map(
                lambda i: world.reset(token, f"fjalekalim-i-ri-{i}-i-gjate"), range(8)
            )
        )
    assert statuses.count(204) == 1 and set(statuses) <= {204, 400}


def test_one_totp_code_opens_exactly_one_of_many_parallel_logins(world):
    from tests.fixtures.accounts import code_for

    secret, _, _ = world.enable_two_factor()
    challenge = world.login().json()["challenge"]
    code = code_for(secret, +1)
    with ThreadPoolExecutor(8) as pool:
        statuses = sorted(
            r.status_code for r in pool.map(lambda _: world.verify(challenge, code), range(8))
        )
    # kufizimi i çiftit mund të ndërhyjë pas disa dështimeve paralele; pohimi i vërtetë është një 200 i vetëm
    assert statuses.count(200) == 1 and set(statuses) <= {200, 401, 429}


def test_one_recovery_code_opens_exactly_one_of_many_parallel_logins(world):
    _, codes, _ = world.enable_two_factor()
    challenge = world.login().json()["challenge"]
    with ThreadPoolExecutor(8) as pool:
        statuses = sorted(
            r.status_code for r in pool.map(lambda _: world.verify(challenge, codes[0]), range(8))
        )
    # kufizimi i çiftit mund të ndërhyjë pas disa dështimeve paralele; pohimi i vërtetë është një 200 i vetëm
    assert statuses.count(200) == 1 and set(statuses) <= {200, 401, 429}


def test_the_whole_flow_and_the_sweep_work_on_postgres(world):
    from analyte import outbox
    from analyte.mail import OutboxMailer
    from tests.fixtures.accounts import EMAIL, NEW_PASSWORD
    from tests.fixtures.mailbox import reset_token_in

    _secret, _, _ = world.enable_two_factor()
    world.forgot()
    assert world.reset(reset_token_in(world.outbox.to(EMAIL)[-1])).status_code == 204
    assert world.login(EMAIL, NEW_PASSWORD).json()["mfa_required"] is True

    # kalimi periodik: një mesazh që s'u dërgua, rilëshohet me token të ri
    class Down:
        def send(self, to, subject, body):
            raise ConnectionRefusedError

    from tests.fixtures.accounts import World

    broken = World(
        world.services.store.root.parent, mailer=Down(), database_url=world.settings.database_url
    )
    broken.forgot()
    working = OutboxMailer()
    report = outbox.resend_unsent(
        broken.services.sessions,
        working,
        broken.settings,
        now=datetime.now(UTC) + timedelta(minutes=11),
        sleep=lambda _s: None,
    )
    assert (report.reissued, report.sent) == (1, 1)
    assert "/reset-password?token=" in working.to(EMAIL)[0].body
