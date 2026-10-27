"""UI 자동화(RPA) 브라우저 대시보드.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
  /       : 대시보드 (명단 확인, 봇 실행, 결과·스크린샷)
  /form   : 자동화 대상 '사내 신청 시스템' (직접 입력해 볼 수도 있음)
"""
import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import auto_fill

BASE = Path(__file__).parent
app = FastAPI(title="UI 자동화 대시보드")


class RunIn(BaseModel):
    show: bool = False  # True면 브라우저 창이 뜨고 천천히 입력하는 모습이 보임


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/form")
def form():
    return FileResponse(BASE / "form.html")


@app.get("/api/applicants")
def applicants():
    auto_fill.ensure_sample_data()
    return auto_fill.read_rows(auto_fill.DATA)


@app.post("/api/run")
def run_bot(body: RunIn):
    # 봇은 별도 프로세스로 실행: 웹 서버와 분리되어 봇이 죽어도 서버는 안전 (실무 RPA 스케줄러와 같은 구조)
    cmd = [sys.executable, str(BASE / "auto_fill.py")] + (["--show"] if body.show else [])
    proc = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, encoding="utf-8", timeout=180,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if proc.returncode != 0:
        raise HTTPException(500, proc.stderr[-800:] or proc.stdout[-800:])
    return {"log": proc.stdout, "results": auto_fill.read_rows(auto_fill.OUT / "result.xlsx")}


@app.get("/screenshot.png")
def screenshot():
    path = auto_fill.OUT / "screenshot.png"
    if not path.exists():
        raise HTTPException(404, "먼저 봇을 실행하세요")
    return FileResponse(path, headers={"Cache-Control": "no-store"})
