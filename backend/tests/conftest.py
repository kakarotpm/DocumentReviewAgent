import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import get_session, init_db
from app.main import app
from app.services.rulebooks import load_builtin_rulebooks


@pytest.fixture
def session():
    """A fresh in-memory database with the built-in rulebooks loaded."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        load_builtin_rulebooks(s, settings.rulebooks_dir)
        yield s


@pytest.fixture
def client(session):
    """API client that uses the in-memory test database."""
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
