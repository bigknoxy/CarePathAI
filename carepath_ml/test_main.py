import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_retrieve_endpoint():
    response = client.post("/retrieve", json={"query": "test"})
    assert response.status_code == 200
    assert response.json() == {"results": []}
