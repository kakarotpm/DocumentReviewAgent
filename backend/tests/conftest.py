import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import get_session, get_session_factory, init_db
from app.main import app
from app.services.rulebooks import load_builtin_rulebooks


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    """Tests never call the real AI: no API key means the demo reviewer is used."""
    monkeypatch.setattr(settings, "anthropic_api_key", "")


@pytest.fixture
def session_factory():
    """A fresh in-memory database with the built-in rulebooks loaded."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    factory = sessionmaker(bind=engine)
    with factory() as s:
        load_builtin_rulebooks(s, settings.rulebooks_dir)
    return factory


@pytest.fixture
def session(session_factory):
    with session_factory() as s:
        yield s


@pytest.fixture
def client(session, session_factory):
    """API client that uses the in-memory test database (background reviews too)."""
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    yield TestClient(app)
    app.dependency_overrides.clear()
