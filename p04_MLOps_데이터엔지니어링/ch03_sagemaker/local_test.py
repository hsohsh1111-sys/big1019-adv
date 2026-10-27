"""AWS 없이 SageMaker의 학습 → 추론 흐름을 로컬에서 그대로 재현한다 (무료).

1) 데이터 준비 (S3 업로드 대신 로컬 폴더)
2) SageMaker와 같은 환경 변수를 설정하고 train.py 실행 (= Training Job)
3) inference.py 의 model_fn → input_fn → predict_fn → output_fn 호출 (= Endpoint 요청)

실행:
  uvicorn web:app --reload   # 브라우저 → http://127.0.0.1:8000
  python local_test.py       # 터미널
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from sklearn.datasets import load_iris

import inference

BASE = Path(__file__).parent
OPT_ML = BASE / "output" / "opt_ml"  # SageMaker 컨테이너의 /opt/ml 을 흉내
COLUMNS = ["sepal_length", "sepal_width", "petal_length", "petal_width"]


def paths(opt_ml=OPT_ML):
    return {"train": opt_ml / "input/data/train", "model": opt_ml / "model", "output": opt_ml / "output/data"}


def run_training_job(n_estimators=50, learning_rate=0.1, opt_ml=OPT_ML):
    """Training Job 흉내: 데이터 채널 준비 → SM_* 환경 변수 → train.py 실행."""
    p = paths(opt_ml)
    p["train"].mkdir(parents=True, exist_ok=True)
    iris = load_iris(as_frame=True)
    df = iris.data.set_axis(COLUMNS, axis=1)
    df["label"] = iris.target
    df.to_csv(p["train"] / "train.csv", index=False)

    env = {**os.environ, "SM_CHANNEL_TRAIN": str(p["train"]), "SM_MODEL_DIR": str(p["model"]),
           "SM_OUTPUT_DATA_DIR": str(p["output"])}
    args = ["--n_estimators", str(n_estimators), "--learning_rate", str(learning_rate)]
    log = subprocess.run([sys.executable, str(BASE / "train.py"), *args], env=env,
                         capture_output=True, text=True, check=True).stdout.strip()
    return {"rows": len(df), "command": "python train.py " + " ".join(args),
            "env": {k: env[k] for k in ("SM_CHANNEL_TRAIN", "SM_MODEL_DIR", "SM_OUTPUT_DATA_DIR")},
            "log": log, "model_files": sorted(f.name for f in p["model"].iterdir()),
            "metrics": json.loads((p["output"] / "metrics.json").read_text())}


def invoke_endpoint(instances, opt_ml=OPT_ML):
    """Endpoint 요청 흉내: 4개 함수를 SageMaker와 같은 순서로 호출하고 단계별 결과를 돌려준다."""
    model = inference.model_fn(paths(opt_ml)["model"])  # 실제 엔드포인트는 서버 시작 시 1번만 호출
    body = json.dumps({"instances": instances})
    parsed = inference.input_fn(body, "application/json")
    prediction = inference.predict_fn(parsed, model)
    return {"request": body, "input_fn": parsed, "predict_fn": prediction,
            "response": inference.output_fn(prediction, "application/json")}


def main():
    job = run_training_job()
    print(f"[1] 학습 데이터 준비: {job['rows']}행 → {job['env']['SM_CHANNEL_TRAIN']}")
    print(f"[2] Training Job 흉내: {job['command']}")
    print("    로그:", job["log"], "| 모델 파일:", job["model_files"])
    result = invoke_endpoint([[5.1, 3.5, 1.4, 0.2], [6.7, 3.0, 5.2, 2.3]])
    print(f"[3] Endpoint 요청 흉내\n    요청: {result['request']}\n    응답: {result['response']}")


if __name__ == "__main__":
    main()
