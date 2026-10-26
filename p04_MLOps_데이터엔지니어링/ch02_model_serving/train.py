"""붓꽃(iris) 분류 모델 학습 → model/model.joblib + model/metadata.json 저장.  실행: python train.py"""
import json
from datetime import datetime
from pathlib import Path

import joblib
import sklearn
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MODEL_DIR = Path(__file__).parent / "model"

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42,
                                                    stratify=iris.target)
model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)).fit(X_train, y_train)
accuracy = accuracy_score(y_test, model.predict(X_test))

MODEL_DIR.mkdir(exist_ok=True)
joblib.dump(model, MODEL_DIR / "model.joblib")
(MODEL_DIR / "metadata.json").write_text(json.dumps({
    "version": datetime.now().strftime("%Y%m%d%H%M"),
    "accuracy": round(accuracy, 4),
    "features": iris.feature_names,
    "classes": iris.target_names.tolist(),
    "sklearn_version": sklearn.__version__,  # 서빙 환경과 버전이 다르면 로딩 오류가 날 수 있어 기록
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"저장 완료: {MODEL_DIR / 'model.joblib'} (accuracy={accuracy:.3f})")
