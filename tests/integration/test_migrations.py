"""
Migrimet dhe skema e modeleve nuk ndahen.

Testet e API-së e ndërtojnë skemën nga modelet (`create_schema`); shërbimi
e ndërton nga migrimet. Po të ndaheshin, testet do të kalonin mbi një
skemë që prodhimi nuk e ka. Ky test e ekzekuton migrimin dhe e krahason
rezultatin me modelet: çdo tabelë e ndryshuar pa migrim e rrëzon atë.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from analyte.persistence.tables import Base

BACKEND = Path(__file__).resolve().parents[2] / "backend"


def _config(url: str) -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_migrations_produce_exactly_the_models(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("ANALYTE_DATABASE_URL", url)
    command.upgrade(_config(url), "head")

    engine = create_engine(url)
    with engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert differences == []


def test_migrations_can_be_undone(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'd.db'}"
    monkeypatch.setenv("ANALYTE_DATABASE_URL", url)
    config = _config(url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(url)
    with engine.connect() as connection:
        tables = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'"
        ).all()
    assert tables == []


def test_0004_keeps_existing_accounts_without_a_second_factor_and_can_be_undone(tmp_path, monkeypatch):
    from sqlalchemy import text

    url = f"sqlite:///{tmp_path / 'u.db'}"
    monkeypatch.setenv("ANALYTE_DATABASE_URL", url)
    config = _config(url)
    command.upgrade(config, "0003")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash, created_at, email_confirmed_at)"
                " VALUES ('11111111-1111-1111-1111-111111111111', 'vjeter@shembull.al', 'x',"
                " '2026-09-01 12:00:00', '2026-09-01 12:00:00')"
            )
        )
    command.upgrade(config, "0004")
    new_tables = {"password_resets", "recovery_codes", "mail_deliveries"}
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT totp_secret_encrypted, totp_enabled_at, totp_last_step FROM users")
        ).one()
        tables = {n for (n,) in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tuple(row) == (None, None, None)
    assert new_tables <= tables

    command.downgrade(config, "0003")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT email FROM users")).scalar() == "vjeter@shembull.al"
        tables = {n for (n,) in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not new_tables & tables
