"""Database connection. Uses SQLite by default; change DATABASE_URL to use PostgreSQL."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """All database models inherit from this."""


def get_db():
    """FastAPI dependency: gives each request its own database session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
