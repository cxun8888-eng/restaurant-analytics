"""Database connection and session helpers for authentication."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


# Docker Compose supplies PostgreSQL in normal development/production runs.
# A local SQLite fallback keeps lightweight unit tests usable without a DB server.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/auth.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
if DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Imported lazily so model metadata is registered before create_all runs.
    from backend.models import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
