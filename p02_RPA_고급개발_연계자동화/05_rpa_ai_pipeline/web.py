"""RPA + AI 파이프라인 브라우저 대시보드.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import pipeline

app = FastAPI(title="RPA + AI 파이프라인")
DOWNLOADS = {"quotes_report.xlsx", "notify.eml"}


class RunIn(BaseModel):
    pages: int = Field(default=1, ge=1, le=3)
    offline: bool = False


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/api/run")
def run(body: RunIn):
    r = pipeline.run(body.pages, body.offline)
    return {
        "source": r["source"], "mode": r["mode"], "count": len(r["df"]), "mail": r["mail"],
        "threshold": pipeline.REVIEW_THRESHOLD,
        "stats": r["stats"].reset_index().to_dict(orient="records"),
        "review": r["review"].to_dict(orient="records"),
        "rows": r["df"].to_dict(orient="records"),
    }


@app.get("/download/{name}")
def download(name: str):
    path = pipeline.OUT / name
    if name not in DOWNLOADS or not path.exists():
        raise HTTPException(404, "먼저 파이프라인을 실행하세요")
    return FileResponse(path, filename=name)
