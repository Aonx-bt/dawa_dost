import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DEMO_MODE"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, SessionLocal, engine, get_db
from app.main import app

get_settings.cache_clear()


@pytest.fixture()
def db_session():
    # app.database.engine is a StaticPool in-memory SQLite engine (see
    # app/database.py), so this is the same database every request/thread
    # sees - which is what lets the scheduler's own SessionLocal() calls
    # observe data written through this fixture.
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
