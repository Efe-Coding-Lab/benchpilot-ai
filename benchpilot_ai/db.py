from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .models import Base

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None
_ENGINE_URL: str | None = None


def get_engine(database_url: str | None = None) -> Engine:
    global _ENGINE, _ENGINE_URL, _SESSION_FACTORY
    url = database_url or get_settings().database_url
    if _ENGINE is None or _ENGINE_URL != url:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _ENGINE = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)
        _ENGINE_URL = url
        _SESSION_FACTORY = sessionmaker(bind=_ENGINE, expire_on_commit=False, future=True)
    return _ENGINE


def init_db(database_url: str | None = None) -> None:
    Base.metadata.create_all(get_engine(database_url))


@contextmanager
def session_scope(database_url: str | None = None) -> Iterator[Session]:
    global _SESSION_FACTORY
    engine = get_engine(database_url)
    if _SESSION_FACTORY is None or _SESSION_FACTORY.kw.get("bind") is not engine:
        _SESSION_FACTORY = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = _SESSION_FACTORY()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
