"""
Mjedisi i Alembic-ut.

URL-ja lexohet vetëm nga `ANALYTE_DATABASE_URL`, jo nga `Settings`: migrimi
nuk ka nevojë për sekretet e shërbimit, dhe kërkimi i tyre këtu do ta
bënte migrimin të pamundur në një makinë që ka vetëm qasje në bazë.
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from analyte.persistence.tables import Base, ExactDecimal, UtcDateTime

DEFAULT_URL = "postgresql+psycopg://analyte:analyte@localhost:5433/analyte"

config = context.config
config.set_main_option("sqlalchemy.url", os.environ.get("ANALYTE_DATABASE_URL", DEFAULT_URL))
target_metadata = Base.metadata


def render_item(kind, item, autogen_context):
    """Tipat e përshtatur shkruhen në migrim si tipat mbi të cilët qëndrojnë.

    Kështu migrimi nuk importon kodin e aplikacionit dhe mbetet i
    ekzekutueshëm edhe pasi `tables.py` ndryshon.
    """
    if kind == "type" and isinstance(item, ExactDecimal):
        return "sa.String(length=64)"
    if kind == "type" and isinstance(item, UtcDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_item=render_item
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
