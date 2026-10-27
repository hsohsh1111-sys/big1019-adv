"""날씨 ETL 파이프라인 브라우저 실습 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import pipeline

app = FastAPI(title="날씨 ETL 파이프라인")


class RunIn(BaseModel):
    days: int = Field(default=7, ge=1, le=30)
    offline: bool = False
    clean_only: bool = False


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/api/run")
def run(body: RunIn):
    try:
        r = pipeline.run(body.days, body.offline, body.clean_only)
    except ValueError as e:  # 데이터 품질 검증 실패
        raise HTTPException(422, str(e)) from e
    return {**r, "daily": r["daily"].to_dict(orient="records")}
