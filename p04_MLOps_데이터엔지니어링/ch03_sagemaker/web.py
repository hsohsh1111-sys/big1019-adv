"""SageMaker 학습·추론 흐름을 로컬에서 체험하는 브라우저 실습 서버 (AWS 비용 0원).

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import local_test

app = FastAPI(title="SageMaker 로컬 체험")


class JobIn(BaseModel):
    n_estimators: int = Field(default=50, ge=1, le=300)
    learning_rate: float = Field(default=0.1, gt=0, le=1)


class InvokeIn(BaseModel):
    instances: list[list[float]] = Field(min_length=1, max_length=20)


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/api/training-job")
def training_job(body: JobIn):
    return local_test.run_training_job(body.n_estimators, body.learning_rate)


@app.post("/api/invoke")
def invoke(body: InvokeIn):
    if not (local_test.paths()["model"] / "model.joblib").exists():
        raise HTTPException(400, "먼저 Training Job을 실행해 모델을 만드세요")
    if any(len(row) != len(local_test.COLUMNS) for row in body.instances):
        raise HTTPException(422, "각 행은 숫자 4개여야 합니다")
    return local_test.invoke_endpoint(body.instances)
