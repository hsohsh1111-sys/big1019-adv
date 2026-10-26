"""⚠ 실제 AWS SageMaker 실행 스크립트 — 요금이 발생할 수 있습니다. (실행 전 README 비용 안내 필독)

준비:
  pip install sagemaker boto3
  aws configure                             # 액세스 키 설정 (IAM 사용자, 최소 권한)
  export SAGEMAKER_ROLE_ARN=arn:aws:iam::<계정ID>:role/<SageMaker 실행 역할>
실행:
  python sagemaker_run.py
"""
import json
import os
import tempfile
from pathlib import Path

from sklearn.datasets import load_iris

ROLE = os.environ.get("SAGEMAKER_ROLE_ARN")
if not ROLE:
    raise SystemExit("SAGEMAKER_ROLE_ARN 환경 변수를 설정하세요. (README 참고)")

import sagemaker  # noqa: E402
from sagemaker.serializers import JSONSerializer  # noqa: E402
from sagemaker.sklearn.estimator import SKLearn  # noqa: E402

session = sagemaker.Session()
BASE = Path(__file__).parent

with tempfile.TemporaryDirectory() as tmp:  # 1) 학습 데이터를 S3에 업로드
    iris = load_iris(as_frame=True)
    df = iris.data.set_axis(["sepal_length", "sepal_width", "petal_length", "petal_width"], axis=1)
    df["label"] = iris.target
    df.to_csv(Path(tmp) / "train.csv", index=False)
    train_s3 = session.upload_data(str(Path(tmp) / "train.csv"), key_prefix="edu-iris/train")
print("S3 업로드:", train_s3)

estimator = SKLearn(  # 2) Training Job — 학습하는 동안만 과금, 끝나면 인스턴스 자동 종료
    entry_point="train.py", source_dir=str(BASE), framework_version="1.2-1", py_version="py3",
    instance_type="ml.m5.large", instance_count=1, role=ROLE,
    hyperparameters={"n_estimators": 50, "learning_rate": 0.1},
    metric_definitions=[{"Name": "validation:accuracy", "Regex": "validation_accuracy=([0-9.]+)"}],
)
estimator.fit({"train": train_s3})
print("모델 위치:", estimator.model_data)

predictor = None
try:  # 3) Endpoint 배포 — 켜져 있는 동안 계속 과금!
    model = estimator.create_model(entry_point="inference.py", source_dir=str(BASE))
    predictor = model.deploy(initial_instance_count=1, instance_type="ml.t2.medium", serializer=JSONSerializer())
    result = predictor.predict({"instances": [[5.1, 3.5, 1.4, 0.2], [6.7, 3.0, 5.2, 2.3]]})
    print("예측 결과:", json.dumps(result, ensure_ascii=False) if not isinstance(result, bytes) else result.decode())
finally:
    if predictor:  # 4) 실습 끝나면 반드시 삭제
        predictor.delete_model()
        predictor.delete_endpoint()
        print("엔드포인트 삭제 완료")
