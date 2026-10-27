from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_counter_increments():
    first = client.get("/api/visit").json()["visits"]
    assert client.get("/api/visit").json()["visits"] == first + 1


def test_index_page():
    res = client.get("/")
    assert res.status_code == 200 and "text/html" in res.headers["content-type"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
