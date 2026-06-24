from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app


class AvailableDatabase:
    def execute(self, statement: object) -> None:
        assert str(statement) == "SELECT 1"


class UnavailableDatabase:
    def execute(self, statement: object) -> None:
        raise SQLAlchemyError("PostgreSQL is unavailable")


def test_health_reports_process_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Expiry Notification API",
        "version": "0.1.0",
        "environment": get_settings().app_environment,
    }


def test_ready_succeeds_when_database_accepts_query() -> None:
    app.dependency_overrides[get_db] = lambda: AvailableDatabase()
    try:
        with TestClient(app) as client:
            response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "available"}


def test_ready_returns_503_when_database_is_unavailable() -> None:
    app.dependency_overrides[get_db] = lambda: UnavailableDatabase()
    try:
        with TestClient(app) as client:
            response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable."}


def test_versioned_health_route_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
