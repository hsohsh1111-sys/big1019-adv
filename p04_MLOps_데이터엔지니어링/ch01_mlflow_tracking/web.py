"""MLflow 실험 추적 브라우저 실습 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
같이 보기: mlflow ui --backend-store-uri sqlite:///mlflow.db  →  http://127.0.0.1:5000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import train

app = FastAPI(title="MLflow 실험 추적")


class TrainIn(BaseModel):
    scale: bool = True
    C: float = Field(default=1.0, gt=0, le=100)  # 규제 강도의 역수: 작을수록 단순한 모델


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/api/runs")
def runs():
    return train.list_runs()


@app.post("/api/train")
def train_one(body: TrainIn):
    return train.train_one(body.scale, body.C)


@app.post("/api/register")
def register():
    if not train.list_runs():
        raise HTTPException(400, "먼저 실험을 1개 이상 실행하세요")
    return {**train.register_best(), **train.predict_champion()}
