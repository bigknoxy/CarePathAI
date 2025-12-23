from fastapi.testclient import TestClient
from carepath_ml.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_retrieve():
    r = client.post("/retrieve", json={"query": "diabetes"})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
    assert "results" in r.json()
