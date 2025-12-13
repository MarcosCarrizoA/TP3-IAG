from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _database_url() -> str:
    # Railway recommended: sqlite:////app/data/app.db
    return os.getenv("DATABASE_URL", "sqlite:///./app.db")


DATABASE_URL = _database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite:"):
    # Required for SQLite with threads (FastAPI default).
    connect_args = {"check_same_thread": False}


engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from db.models import Base  # local import to avoid import cycles

    Base.metadata.create_all(bind=engine)


