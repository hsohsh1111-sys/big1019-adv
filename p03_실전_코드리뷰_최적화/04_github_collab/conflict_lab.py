"""Git 충돌(Conflict) 연습장: 임시 폴더에 저장소를 만들고 두 브랜치가 같은 줄을 고쳐 충돌을 일으킨다.

실행:
  uvicorn web:app --reload   # 브라우저에서 충돌 만들기 → 해결 → 커밋 → http://127.0.0.1:8000
  python conflict_lab.py     # 터미널: 출력된 폴더로 이동해 직접 해결
Git만 있으면 되고, GitHub 계정·인터넷은 필요 없다.
"""
import subprocess
import tempfile
from pathlib import Path

MARKERS = ("<<<<<<<", "=======", ">>>>>>>")


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def create_lab():
    """충돌이 난 상태의 연습 저장소를 만들고 (저장소 경로, merge 출력)을 반환."""
    repo = Path(tempfile.mkdtemp(prefix="conflict_lab_"))
    git("init", "-b", "main", cwd=repo)
    git("config", "user.name", "Lab User", cwd=repo)  # 연습 저장소 안에서만 쓰는 이름
    git("config", "user.email", "lab@example.com", cwd=repo)

    price = repo / "price.py"
    price.write_text("SHIPPING_FEE = 3000\nFREE_SHIPPING = 50000\n", encoding="utf-8")
    git("add", ".", cwd=repo)
    git("commit", "-m", "feat: 배송비 정책 추가", cwd=repo)

    git("switch", "-c", "feature/promo", cwd=repo)  # 팀원 A: 프로모션으로 무료배송 기준 인하
    price.write_text("SHIPPING_FEE = 3000\nFREE_SHIPPING = 30000  # 연말 프로모션\n", encoding="utf-8")
    git("commit", "-am", "feat: 연말 무료배송 기준 3만원", cwd=repo)

    git("switch", "main", cwd=repo)  # 팀원 B: 비용 증가로 무료배송 기준 인상
    price.write_text("SHIPPING_FEE = 3000\nFREE_SHIPPING = 70000  # 물류비 인상\n", encoding="utf-8")
    git("commit", "-am", "fix: 물류비 인상 반영", cwd=repo)

    result = git("merge", "feature/promo", cwd=repo)
    return repo, result.stdout or result.stderr


def resolve(repo, content, message="merge: 무료배송 기준 충돌 해결"):
    """충돌 표시가 없는 내용으로 price.py를 저장하고 merge 커밋을 만든다."""
    if any(m in content for m in MARKERS):
        raise ValueError("충돌 표시(<<<<<<< ======= >>>>>>>)가 아직 남아 있습니다")
    (repo / "price.py").write_text(content, encoding="utf-8")
    git("add", "price.py", cwd=repo)
    result = git("commit", "-m", message, cwd=repo)
    if result.returncode != 0:
        raise ValueError(result.stdout or result.stderr)
    return graph(repo)


def graph(repo):
    return git("log", "--oneline", "--graph", "--all", cwd=repo).stdout


def main():
    repo, merge_output = create_lab()
    print(merge_output)
    print("─" * 60)
    print((repo / "price.py").read_text(encoding="utf-8"))
    print("─" * 60)
    print(f"""충돌 연습 저장소: {repo}

해결 순서:
  1) cd "{repo}"
  2) git status                 # 충돌 파일 확인 (both modified)
  3) price.py 를 열어 <<<<<<< ======= >>>>>>> 표시를 지우고 올바른 값만 남기기
     (실무라면 두 작성자와 상의해서 결정!)
  4) git add price.py
  5) git commit -m "merge: 무료배송 기준 충돌 해결"
  6) git log --oneline --graph --all   # 합쳐진 이력 확인""")


if __name__ == "__main__":
    main()
