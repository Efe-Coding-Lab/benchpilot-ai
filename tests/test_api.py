from __future__ import annotations

from fastapi.testclient import TestClient

from benchpilot_ai.api import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
