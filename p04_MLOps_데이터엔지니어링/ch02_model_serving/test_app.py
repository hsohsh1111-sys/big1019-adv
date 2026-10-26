"""서빙 API 테스트.  실행: python train.py && pytest -q"""
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_predict_setosa_and_virginica():
    body = {"items": [
        {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
        {"sepal_length": 7.7, "sepal_width": 3.0, "petal_length": 6.1, "petal_width": 2.3},
    ]}
    res = client.post("/predict", json=body)
    assert res.status_code == 200
    assert [p["class"] for p in res.json()["predictions"]] == ["setosa", "virginica"]


def test_invalid_input_rejected():
    bad = {"items": [{"sepal_length": -1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}]}
    assert client.post("/predict", json=bad).status_code == 422
    assert client.post("/predict", json={"items": []}).status_code == 422
