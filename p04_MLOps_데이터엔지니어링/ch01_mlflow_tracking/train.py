"""MLflow 실험 추적: 하이퍼파라미터를 바꿔가며 학습 → 기록 → 최고 모델을 레지스트리에 등록 → 불러와 예측.

실행:
  python train.py                                            # 실험 10개 일괄 실행 + 등록
  uvicorn web:app --reload                                   # 브라우저에서 실험 추가 → http://127.0.0.1:8000
확인:
  mlflow ui --backend-store-uri sqlite:///mlflow.db          # MLflow 화면 → http://127.0.0.1:5000
"""
import itertools
import warnings
from pathlib import Path

import mlflow
from mlflow.models import infer_signature
from sklearn.datasets import load_wine
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")  # 실습 출력이 깔끔하도록 경고 숨김 (스케일링 안 한 실험의 수렴 경고 등)
BASE = Path(__file__).parent
mlflow.set_tracking_uri(f"sqlite:///{(BASE / 'mlflow.db').as_posix()}")  # 실험 기록 DB (로컬 파일)
mlflow.set_experiment("wine-classification")
MODEL_NAME = "wine-classifier"

X, y = load_wine(return_X_y=True, as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)


def train_one(scale, C):
    """실험(run) 1개: 학습 → 설정·성능·모델을 MLflow에 기록."""
    with mlflow.start_run(run_name=f"lr_scale{int(scale)}_C{C}") as run:
        params = {"scaling": scale, "C": C, "max_iter": 5000}
        clf = LogisticRegression(C=C, max_iter=5000)
        model = (make_pipeline(StandardScaler(), clf) if scale else clf).fit(X_train, y_train)
        pred = model.predict(X_test)
        metrics = {"accuracy": accuracy_score(y_test, pred), "f1_macro": f1_score(y_test, pred, average="macro")}

        mlflow.log_params(params)  # ① 설정
        mlflow.log_metrics(metrics)  # ② 성능
        mlflow.set_tag("dataset", "sklearn-wine")
        mlflow.sklearn.log_model(  # ③ 모델 파일 + 입력 형식(signature)
            model, name="model", signature=infer_signature(X_train, pred), input_example=X_train.head(2))
    return {"run_id": run.info.run_id, "name": run.info.run_name, **params,
            **{k: round(v, 4) for k, v in metrics.items()}}


def list_runs():
    """기록된 실험 목록 (f1 높은 순)."""
    df = mlflow.search_runs(order_by=["metrics.f1_macro DESC"])
    return [{"run_id": r["run_id"], "name": r.get("tags.mlflow.runName"), "scaling": r.get("params.scaling"),
             "C": r.get("params.C"), "accuracy": round(r["metrics.accuracy"], 4),
             "f1_macro": round(r["metrics.f1_macro"], 4)} for _, r in df.iterrows()]


def register_best():
    """f1이 가장 높은 실험의 모델을 레지스트리에 등록하고 'champion' 별칭 부여 (= 운영 모델)."""
    best = list_runs()[0]
    version = mlflow.register_model(f"runs:/{best['run_id']}/model", MODEL_NAME)
    mlflow.MlflowClient().set_registered_model_alias(MODEL_NAME, "champion", version.version)
    return {**best, "version": version.version}


def predict_champion(n=5):
    # 서비스 코드는 '버전 번호'가 아니라 '별칭'으로 모델을 불러온다 → 모델 교체 시 코드 수정 불필요
    champion = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@champion")
    return {"predictions": champion.predict(X_test.head(n)).tolist(), "answers": y_test.head(n).tolist()}


def main():
    for scale, C in itertools.product([False, True], [0.001, 0.01, 0.1, 1, 10]):
        r = train_one(scale, C)
        print(f"{r['name']:<20} accuracy={r['accuracy']:.3f}  f1={r['f1_macro']:.3f}")
    best = register_best()
    print(f"\n최고 모델: {best['name']} (f1={best['f1_macro']:.3f}) → {MODEL_NAME} v{best['version']} @champion")
    result = predict_champion()
    print("champion 모델 예측 (테스트 5건):", result["predictions"], "/ 정답:", result["answers"])


if __name__ == "__main__":
    main()
