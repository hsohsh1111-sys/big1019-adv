"""✅ legacy_app.py 를 정적 분석 결과대로 고친 코드 — `ruff check fixed_app.py` 결과 0건."""
import ast
import os
import shutil
from pathlib import Path

DB_PASSWORD = os.environ.get("DB_PASSWORD", "")  # 비밀 값은 코드가 아니라 환경 변수로
GRADE_CUTS = [(95, "A+"), (90, "A"), (80, "B"), (70, "C"), (60, "D")]


def get_user(conn, username):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name = ?", (username,))  # 파라미터 바인딩 → 인젝션 차단
    return cur.fetchone()


def add_tag(tag, tags=None):  # 기본값에 리스트 같은 가변 객체 금지 → None 으로 받고 새로 만든다
    tags = [] if tags is None else tags
    tags.append(tag)
    return tags


def run_backup(path):
    return shutil.make_archive("backup", "gztar", root_dir=path)  # 셸 명령 대신 파이썬 기능 사용


def grade(score):
    return next((g for cut, g in GRADE_CUTS if score >= cut), "F")  # 중첩 if → 표(데이터)로


def load_config(path):
    # eval 대신 리터럴(숫자·문자열·리스트·딕셔너리)만 해석, read_text 는 파일을 자동으로 닫는다
    return ast.literal_eval(Path(path).read_text(encoding="utf-8"))
