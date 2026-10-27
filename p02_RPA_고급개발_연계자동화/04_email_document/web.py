"""메일 머지 브라우저 실습 서버. 테스트 메일 서버(127.0.0.1:1025)를 함께 실행한다.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

import mail_merge
import mail_server

BASE = Path(__file__).parent


@asynccontextmanager
async def lifespan(app):
    try:
        server = mail_server.start()  # 서버 시작 시 테스트 메일 서버도 같이 켠다
        print(f"테스트 메일 서버 시작: {mail_server.HOST}:{mail_server.PORT}")
    except OSError:
        server = None
        print("1025 포트 사용 중 → 이미 실행 중인 mail_server.py 를 사용합니다")
    yield
    if server:
        server.stop()


app = FastAPI(title="메일 머지 & 수료증 자동화", lifespan=lifespan)


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/api/members")
def members():
    return mail_merge.read_members()


@app.post("/api/send")
def send():
    try:
        return mail_merge.send_all()
    except ConnectionError as e:
        raise HTTPException(503, str(e)) from e


@app.get("/api/inbox")
def inbox():
    return mail_server.read_inbox()


@app.get("/download/{name}")
def download(name: str):
    path = mail_merge.OUT / name
    # 파일 이름만 허용(경로 조작 방지) + 생성된 결과물만 내려받기
    if Path(name).name != name or path.suffix not in (".docx", ".xlsx") or not path.exists():
        raise HTTPException(404, "파일이 없습니다")
    return FileResponse(path, filename=name)
