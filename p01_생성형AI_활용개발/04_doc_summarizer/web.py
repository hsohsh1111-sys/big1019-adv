"""회의록 요약 & 보고서 생성 브라우저 실습 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import summarize

BASE = Path(__file__).parent
app = FastAPI(title="회의록 요약기")


class Document(BaseModel):
    text: str = Field(min_length=20, max_length=30000)


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/api/sample")
def sample():
    return {"text": (BASE / "sample_meeting.txt").read_text(encoding="utf-8")}


@app.post("/api/summarize")
def run(doc: Document):
    return summarize.summarize(doc.text)
