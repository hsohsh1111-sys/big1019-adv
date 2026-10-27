"""GitHub 협업 브라우저 실습 서버: 충돌 해결 연습 + 협업 템플릿 미리보기.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import conflict_lab

BASE = Path(__file__).parent
app = FastAPI(title="GitHub 협업 실습")
LAB = {"repo": None}  # 현재 연습 중인 저장소 (1인 실습용)


class Resolution(BaseModel):
    content: str


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.post("/api/lab")
def create_lab():
    repo, merge_output = conflict_lab.create_lab()
    LAB["repo"] = repo
    return {"repo": str(repo), "merge": merge_output,
            "status": conflict_lab.git("status", "--short", cwd=repo).stdout,
            "content": (repo / "price.py").read_text(encoding="utf-8"),
            "graph": conflict_lab.graph(repo)}


@app.post("/api/resolve")
def resolve(body: Resolution):
    if LAB["repo"] is None:
        raise HTTPException(400, "먼저 충돌을 만드세요")
    try:
        return {"graph": conflict_lab.resolve(LAB["repo"], body.content)}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.get("/api/templates")
def templates():
    files = sorted(p for p in (BASE / ".github").rglob("*") if p.is_file())
    return [{"path": p.relative_to(BASE).as_posix(), "content": p.read_text(encoding="utf-8")} for p in files]
