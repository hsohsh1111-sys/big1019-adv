"""LangChain 에이전트 & 파이프라인 브라우저 실습 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import agent
import pipeline

app = FastAPI(title="LangChain 에이전트 & 파이프라인")


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=300)


class Article(BaseModel):
    article: str = Field(min_length=10, max_length=5000)


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/api/sample")
def sample():
    return {"article": pipeline.ARTICLE.strip()}


@app.post("/api/agent")
def run_agent(body: Question):
    return agent.run_agent(body.question)


@app.post("/api/pipeline")
def run_pipeline(body: Article):
    return pipeline.run_pipeline(body.article)
