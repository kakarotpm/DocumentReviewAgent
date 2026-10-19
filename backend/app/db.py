"""Database connection. SQLite by default; set DATABASE_URL in .env to use PostgreSQL."""

from sqlalchemy import create_engine
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


def init_db(bind=engine):
    """Create any tables that don't exist yet."""
    from app import models  # noqa: F401  (registers the tables)

    Base.metadata.create_all(bind)
