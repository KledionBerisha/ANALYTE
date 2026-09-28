"""
Lidhja me bazën dhe sesionet.

SQLAlchemy sinkron, jo asinkron: FastAPI i ekzekuton pikat fundore
sinkrone në një grup fijesh, dhe e gjithë logjika e përpunimit — leximi i
PDF-së, OCR-ja, rregullat — është sinkrone gjithsesi. Një shtresë asinkrone
këtu do të shtonte kompleksitet pa fitim.

SQLite përdoret vetëm në teste; aty çelësat e huaj duhen ndezur me dorë,
përndryshe fshirja në kaskadë nuk ndodh dhe testi i fshirjes do të
kalonte për arsye të gabuar.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .tables import Base


def make_engine(url: str) -> Engine:
    engine = create_engine(url, future=True)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    """Vetëm për teste dhe prova lokale. Në shërbim skema vjen nga Alembic."""
    Base.metadata.create_all(engine)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
