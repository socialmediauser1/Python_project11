import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, app, get_db

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

@pytest.fixture()
def client() -> TestClient:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    app.state.TestingSessionLocal = TestingSessionLocal
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    app.state.pop("TestingSessionLocal", None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture()
def session_maker(client):
    return app.state.TestingSessionLocal

@pytest.fixture()
def user_factory(client):
    def _create(name: str, email: str):
        response = client.post("/users", json={"name": name, "email": email})
        assert response.status_code == 201
        return response.json()
    return _create