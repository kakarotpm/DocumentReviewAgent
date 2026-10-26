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

    # Small updates for databases created by earlier versions of the app.
    rule_result_columns = [c["name"] for c in inspect(bind).get_columns("rule_results")]
    version_columns = [c["name"] for c in inspect(bind).get_columns("document_versions")]
    changes = []
    # 2026-10-21: rules no longer have a category (the old column was required, which would block saves).
    if "category" in rule_result_columns:
        changes.append("ALTER TABLE rule_results DROP COLUMN category")
    # 2026-10-26: Part B rules check an optional Excel workbook.
    if "part" not in rule_result_columns:
        changes.append("ALTER TABLE rule_results ADD COLUMN part VARCHAR(10) NOT NULL DEFAULT 'document'")
    if "workbook_filename" not in version_columns:
        changes.append("ALTER TABLE document_versions ADD COLUMN workbook_filename VARCHAR(300)")
    if "workbook_text" not in version_columns:
        changes.append("ALTER TABLE document_versions ADD COLUMN workbook_text TEXT")
    if changes:
        with bind.begin() as connection:
            for change in changes:
                connection.execute(text(change))
