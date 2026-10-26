from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_counter_increments():
    first = client.get("/").json()["visits"]
    assert client.get("/").json()["visits"] == first + 1


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
