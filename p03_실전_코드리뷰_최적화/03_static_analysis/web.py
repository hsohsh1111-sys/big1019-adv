"""정적 분석 브라우저 실습 서버: ruff 결과 보기 + SQL 인젝션 체험.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse

import fixed_app
import legacy_app

BASE = Path(__file__).parent
app = FastAPI(title="정적 분석 실습")
FileName = Literal["legacy_app.py", "fixed_app.py"]  # 분석·조회 가능한 파일만 허용


def make_db():
    """요청마다 새로 만드는 메모리 DB (실습용 사용자 3명)."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT, role TEXT, email TEXT)")
    conn.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", [
        (1, "admin", "관리자", "admin@corp.example"), (2, "kim", "회원", "kim@example.com"),
        (3, "lee", "회원", "lee@example.com")])
    return conn


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/api/code")
def code(file: FileName):
    return {"code": (BASE / file).read_text(encoding="utf-8")}


@app.get("/api/ruff")
def ruff(file: FileName):
    # 실행 인자가 고정 목록(sys.executable, 허용된 파일명)이라 안전하다고 검토함 → noqa 로 표시
    proc = subprocess.run([sys.executable, "-m", "ruff", "check", file, "--output-format", "json"],  # noqa: S603
                          cwd=BASE, capture_output=True, text=True, encoding="utf-8")
    if not proc.stdout.strip().startswith("["):
        error = proc.stderr or "ruff 를 실행할 수 없습니다 (pip install ruff)"
        return {"error": error, "findings": []}
    findings = [{"code": f["code"], "line": f["location"]["row"], "message": f["message"],
                 "url": f.get("url")} for f in json.loads(proc.stdout)]
    return {"error": None, "findings": sorted(findings, key=lambda f: f["line"])}


@app.get("/api/users")
def find_user(name: str, mode: Literal["unsafe", "safe"]):
    conn = make_db()
    try:
        row = (legacy_app if mode == "unsafe" else fixed_app).get_user(conn, name)
        return {"row": row, "error": None}
    except sqlite3.Error as e:
        return {"row": None, "error": str(e)}
    finally:
        conn.close()
