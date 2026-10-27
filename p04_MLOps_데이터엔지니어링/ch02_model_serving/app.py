"""모델 서빙 API (FastAPI).

실행: python train.py  →  uvicorn app:app --reload
  http://127.0.0.1:8000       : 예측 화면
  http://127.0.0.1:8000/docs  : API 문서
"""
import json
import time
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE = Path(__file__).parent
MODEL_DIR = BASE / "model"
if not (MODEL_DIR / "model.joblib").exists():
    raise RuntimeError("모델 파일이 없습니다. 먼저 `python train.py` 를 실행하세요.")

model = joblib.load(MODEL_DIR / "model.joblib")  # 서버 시작 시 1번만 로딩 (요청마다 로딩하면 느림)
meta = json.loads((MODEL_DIR / "metadata.json").read_text(encoding="utf-8"))
app = FastAPI(title="Iris 분류 API", version=meta["version"])


class Flower(BaseModel):
    sepal_length: float = Field(gt=0, lt=20, examples=[5.1])
    sepal_width: float = Field(gt=0, lt=20, examples=[3.5])
    petal_length: float = Field(gt=0, lt=20, examples=[1.4])
    petal_width: float = Field(gt=0, lt=20, examples=[0.2])


class Batch(BaseModel):
    items: list[Flower] = Field(min_length=1, max_length=100)


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "model_version": meta["version"]}


@app.get("/model-info")
def model_info():
    return meta


@app.post("/predict")
def predict(batch: Batch):
    start = time.perf_counter()
    rows = [[f.sepal_length, f.sepal_width, f.petal_length, f.petal_width] for f in batch.items]
    try:
        probs = model.predict_proba(rows)
    except Exception as e:
        raise HTTPException(500, f"예측 실패: {e}") from e
    results = [{"class": meta["classes"][p.argmax()], "probability": round(float(p.max()), 4),
                "probabilities": {c: round(float(v), 4) for c, v in zip(meta["classes"], p, strict=True)}}
               for p in probs]
    return {"model_version": meta["version"], "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            "predictions": results}
