"""Database connection. SQLite by default; set DATABASE_URL in .env to use PostgreSQL."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session():
    """FastAPI dependency: one database session per request."""
    with SessionLocal() as session:
        yield session


def get_session_factory():
    """FastAPI dependency: how background tasks open their own database session."""
    return SessionLocal


def init_db(bind=engine):
    """Create any tables that don't exist yet, and apply small updates to older databases."""
    from app import models  # noqa: F401  (registers the tables)

    Base.metadata.create_all(bind)

    # 2026-10-21: rules no longer have a category. Databases created before then still have a
    # required category column on rule_results, which would stop new results being saved.
    columns = [c["name"] for c in inspect(bind).get_columns("rule_results")]
    if "category" in columns:
        with bind.begin() as connection:
            connection.execute(text("ALTER TABLE rule_results DROP COLUMN category"))
