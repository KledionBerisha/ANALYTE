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
