"""Basic smoke tests for the FastAPI application."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    """Health endpoint should return HTTP 200 with status ok."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

