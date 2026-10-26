"""API 동작 테스트: pytest test_app.py  (임시 DB 사용, 키 없이 모의 모드로 실행)"""
import importlib
import os

from fastapi.testclient import TestClient


def make_client(tmp_path):
    os.environ["NOTES_DB"] = str(tmp_path / "test.db")
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GOOGLE_API_KEY", None)
    import app

    return TestClient(importlib.reload(app).app)


def test_create_search_ask_delete(tmp_path):
    client = make_client(tmp_path)
    r = client.post("/notes", json={"content": "금요일 오후 3시 팀 회의, 회의 안건은 배포 일정"})
    assert r.status_code == 201
    note = r.json()
    assert note["summary"] and note["tags"] and note["ai_source"] == "mock"

    assert len(client.get("/notes").json()) == 1
    assert len(client.get("/notes", params={"tag": "회의"}).json()) == 1
    assert client.get("/notes", params={"tag": "' OR 1=1 --"}).json() == []  # SQL 인젝션 시도는 결과 없음

    answer = client.post("/ask", json={"question": "회의 언제야?"}).json()
    assert answer["sources"] == [note["id"]]

    assert client.delete(f"/notes/{note['id']}").status_code == 204
    assert client.delete(f"/notes/{note['id']}").status_code == 404


def test_validation(tmp_path):
    client = make_client(tmp_path)
    assert client.post("/notes", json={"content": ""}).status_code == 422
