"""AWS 없이 SageMaker의 학습 → 추론 흐름을 로컬에서 그대로 재현한다 (무료).

1) 데이터 준비 (S3 업로드 대신 로컬 폴더)
2) SageMaker와 같은 환경 변수를 설정하고 train.py 실행 (= Training Job)
3) inference.py 의 model_fn → input_fn → predict_fn → output_fn 호출 (= Endpoint 요청)

실행: python local_test.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from sklearn.datasets import load_iris

import inference

BASE = Path(__file__).parent

with tempfile.TemporaryDirectory() as tmp:
    opt_ml = Path(tmp) / "opt" / "ml"  # SageMaker 컨테이너의 /opt/ml 을 흉내
    train_dir, model_dir, output_dir = opt_ml / "input/data/train", opt_ml / "model", opt_ml / "output/data"
    train_dir.mkdir(parents=True)

    iris = load_iris(as_frame=True)
    df = iris.data.set_axis(["sepal_length", "sepal_width", "petal_length", "petal_width"], axis=1)
    df["label"] = iris.target
    df.to_csv(train_dir / "train.csv", index=False)
    print(f"[1] 학습 데이터 준비: {len(df)}행 → {train_dir}")

    env = {**os.environ, "SM_CHANNEL_TRAIN": str(train_dir), "SM_MODEL_DIR": str(model_dir),
           "SM_OUTPUT_DATA_DIR": str(output_dir)}
    cmd = [sys.executable, str(BASE / "train.py"), "--n_estimators", "50", "--learning_rate", "0.1"]
    print(f"[2] Training Job 흉내: train.py {' '.join(cmd[2:])}")
    out = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True).stdout
    print("    로그:", out.strip(), "| 모델 파일:", [p.name for p in model_dir.iterdir()])

    model = inference.model_fn(model_dir)
    body = json.dumps({"instances": [[5.1, 3.5, 1.4, 0.2], [6.7, 3.0, 5.2, 2.3]]})
    response = inference.output_fn(inference.predict_fn(inference.input_fn(body), model))
    print(f"[3] Endpoint 요청 흉내\n    요청: {body}\n    응답: {response}")
