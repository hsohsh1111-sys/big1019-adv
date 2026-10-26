"""SageMaker 추론 스크립트 — 엔드포인트가 요청을 받을 때 호출하는 4개 함수 규약.

model_fn  : 서버 시작 시 1번, 모델 로딩
input_fn  : 요청 본문(JSON) → 모델 입력
predict_fn: 예측
output_fn : 결과 → 응답 본문(JSON)
"""
import json
from pathlib import Path

import joblib

CLASSES = ["setosa", "versicolor", "virginica"]


def model_fn(model_dir):
    return joblib.load(Path(model_dir) / "model.joblib")


def input_fn(request_body, content_type="application/json"):
    if content_type != "application/json":
        raise ValueError(f"지원하지 않는 형식: {content_type}")
    data = json.loads(request_body)
    return data["instances"]


def predict_fn(instances, model):
    import pandas as pd

    df = pd.DataFrame(instances, columns=["sepal_length", "sepal_width", "petal_length", "petal_width"])
    return [{"class": CLASSES[int(c)], "probability": round(float(p.max()), 4)}
            for c, p in zip(model.predict(df), model.predict_proba(df), strict=True)]


def output_fn(prediction, accept="application/json"):
    return json.dumps({"predictions": prediction}, ensure_ascii=False)
