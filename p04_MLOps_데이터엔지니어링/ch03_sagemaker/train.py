"""SageMaker 스크립트 모드 학습 스크립트 — 로컬과 SageMaker에서 똑같이 동작한다.

SageMaker는 이 파일을 컨테이너에서 `python train.py --n_estimators 100 ...` 처럼 실행하고,
데이터 위치·모델 저장 위치를 환경 변수(SM_CHANNEL_TRAIN, SM_MODEL_DIR)로 알려준다.
로컬에서는 환경 변수가 없으므로 기본값(data/, model/)을 사용한다.
"""
import argparse
import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

BASE = Path(__file__).parent


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--n_estimators", type=int, default=100)  # 하이퍼파라미터: estimator에서 전달
    p.add_argument("--learning_rate", type=float, default=0.1)
    p.add_argument("--train", default=os.environ.get("SM_CHANNEL_TRAIN", str(BASE / "data")))
    p.add_argument("--model-dir", default=os.environ.get("SM_MODEL_DIR", str(BASE / "model")))
    p.add_argument("--output-dir", default=os.environ.get("SM_OUTPUT_DATA_DIR", str(BASE / "output")))
    return p.parse_args()


def main():
    args = parse_args()
    df = pd.read_csv(Path(args.train) / "train.csv")
    X, y = df.drop(columns="label"), df["label"]
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = GradientBoostingClassifier(n_estimators=args.n_estimators, learning_rate=args.learning_rate,
                                       random_state=42).fit(X_train, y_train)
    accuracy = accuracy_score(y_val, model.predict(X_val))
    print(f"validation_accuracy={accuracy:.4f}")  # SageMaker는 로그에서 정규식으로 지표를 수집할 수 있음

    Path(args.model_dir).mkdir(parents=True, exist_ok=True)
    joblib.dump(model, Path(args.model_dir) / "model.joblib")  # SM_MODEL_DIR → S3 model.tar.gz 로 업로드됨
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    (Path(args.output_dir) / "metrics.json").write_text(json.dumps({"validation_accuracy": accuracy}))


if __name__ == "__main__":
    main()
