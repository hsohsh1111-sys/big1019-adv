"""웹 스크래핑 브라우저 실습 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import scrape_books

app = FastAPI(title="책 정보 스크래퍼")
DOWNLOADS = {"books.csv", "books.xlsx"}  # 내려받을 수 있는 파일만 허용 (경로 조작 방지)


class ScrapeIn(BaseModel):
    pages: int = Field(default=1, ge=1, le=5)  # 연습 사이트라도 과도한 수집은 금지


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/api/scrape")
def scrape(body: ScrapeIn):
    try:
        df = scrape_books.scrape(body.pages, delay=1.0)
    except RuntimeError as e:
        raise HTTPException(502, f"{e} (인터넷 연결을 확인하세요)") from e
    stats = scrape_books.save(df)
    top = df.sort_values(["평점", "가격(£)"], ascending=[False, True]).head(5)
    return {
        "count": len(df),
        "books": df.to_dict(orient="records"),
        "stats": stats.reset_index().to_dict(orient="records"),
        "top": top.to_dict(orient="records"),
    }


@app.get("/download/{name}")
def download(name: str):
    path = scrape_books.OUT / name
    if name not in DOWNLOADS or not path.exists():
        raise HTTPException(404, "먼저 수집을 실행하세요")
    return FileResponse(path, filename=name)
