"""AI 파일 정리 자동화 브라우저 실습 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
흐름: 자연어 → [계획 만들기] → (계획 JSON 직접 수정 가능) → [검증 & 미리보기] → [실행]
"""
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import run

BASE = Path(__file__).parent
app = FastAPI(title="AI 파일 정리 자동화")


class RequestIn(BaseModel):
    request: str = Field(min_length=1, max_length=300)


class PlanIn(BaseModel):
    plan: Any  # 일부러 형식을 제한하지 않음 → 어떤 계획이 와도 run.validate()가 걸러내는지 확인


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/api/files")
def files():
    return run.list_files()


@app.post("/api/reset")
def reset():
    run.reset_sandbox()
    return run.list_files()


@app.post("/api/plan")
def make_plan(body: RequestIn):
    plan, source = run.make_plan(body.request)
    return {"plan": plan, "source": source}


@app.get("/api/evil-plan")
def evil_plan():
    return {"plan": json.loads((BASE / "evil_plan.json").read_text(encoding="utf-8")), "source": "evil_plan.json"}


@app.post("/api/check")
def check(body: PlanIn):
    errors = run.validate(body.plan)
    return {"errors": errors, "changes": [] if errors else run.execute(body.plan, apply=False)}


@app.post("/api/apply")
def apply(body: PlanIn):
    # 브라우저에서 '검증 통과'를 봤더라도 서버는 다시 검증한다 (클라이언트는 언제든 조작 가능)
    try:
        changes = run.apply_plan(body.plan, "웹 실행")
    except (ValueError, OSError) as e:
        raise HTTPException(400, str(e)) from e
    return {"changes": changes, "files": run.list_files()}
