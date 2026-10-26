"""자연어 지시 → (LLM) JSON 실행 계획 → 검증 → 미리보기 → 실행 하는 안전한 파일 정리 자동화.

실행:
  python run.py "pdf는 documents 폴더로 옮기고 이름 앞에 오늘 날짜를 붙여줘"        # 미리보기(dry-run)
  python run.py "pdf는 documents 폴더로 옮기고 이름 앞에 오늘 날짜를 붙여줘" --yes  # 실제 실행
  python run.py --plan evil_plan.json                                                # 위험한 계획이 거부되는지 확인
  python run.py --reset                                                              # 연습 폴더 초기화

모든 작업은 sandbox/ 폴더 안에서만 실행된다. GEMINI_API_KEY 가 없으면 규칙 기반 파서가 계획을 만든다.
"""
import argparse
import json
import os
import re
import shutil
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).parent
SANDBOX = BASE / "sandbox"
LOG = BASE / "run.log"
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
MAX_STEPS = 20

ALLOWED = {
    "mkdir": ["path"],
    "move": ["src", "dst"],
    "rename_prefix": ["pattern", "prefix"],
}
PROMPT = """너는 파일 정리 자동화 도우미다. 사용자 요청을 아래 작업만 사용해 JSON 배열로 답하라.
- {"action": "mkdir", "path": "폴더"}
- {"action": "move", "src": "glob 패턴(예: *.pdf)", "dst": "폴더"}
- {"action": "rename_prefix", "pattern": "glob 패턴(예: documents/*.pdf)", "prefix": "접두어"}
오늘 날짜는 {today} 이다. 설명 없이 JSON 배열만 출력하라.
요청: {request}"""


def reset_sandbox():
    shutil.rmtree(SANDBOX, ignore_errors=True)
    SANDBOX.mkdir()
    for name in ["report.pdf", "invoice_10월.pdf", "photo1.jpg", "photo2.png", "memo.txt", "data.xlsx"]:
        (SANDBOX / name).write_text(f"sample file: {name}", encoding="utf-8")
    print(f"연습 폴더 초기화: {sorted(p.name for p in SANDBOX.iterdir())}")


# ------------------------------------------------------------------ 1. 계획 만들기
def plan_with_llm(request):
    from google import genai
    from google.genai import types

    text = genai.Client().models.generate_content(
        model=MODEL,
        contents=PROMPT.replace("{today}", date.today().isoformat()).replace("{request}", request),
        config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
    ).text
    return json.loads(text)


def plan_with_rules(request):
    """키가 없을 때: 간단한 규칙으로 자연어를 계획으로 바꾼다."""
    ext_map = {"pdf": "*.pdf", "이미지": "*.[jp][pn]g", "사진": "*.[jp][pn]g", "엑셀": "*.xlsx", "텍스트": "*.txt"}
    plan = []
    folder = (re.search(r"([A-Za-z0-9_가-힣]+)\s*폴더", request) or [None, "sorted"])[1]
    for word, pattern in ext_map.items():
        if word in request.lower():
            plan += [{"action": "mkdir", "path": folder}, {"action": "move", "src": pattern, "dst": folder}]
            if "날짜" in request:
                plan.append({"action": "rename_prefix", "pattern": f"{folder}/{pattern}",
                             "prefix": date.today().isoformat() + "_"})
            break
    return plan


# ------------------------------------------------------------------ 2. 검증 (가드레일)
def inside_sandbox(rel):
    return (SANDBOX / rel).resolve().is_relative_to(SANDBOX.resolve())


def validate(plan):
    errors = []
    if not isinstance(plan, list) or not plan:
        return ["계획이 비어 있거나 배열이 아닙니다"]
    if len(plan) > MAX_STEPS:
        errors.append(f"작업 수가 너무 많습니다 ({len(plan)} > {MAX_STEPS})")
    for i, step in enumerate(plan, 1):
        action = step.get("action") if isinstance(step, dict) else None
        if action not in ALLOWED:
            errors.append(f"{i}번: 허용되지 않은 작업 '{action}'")
            continue
        missing = [k for k in ALLOWED[action] if not step.get(k)]
        if missing:
            errors.append(f"{i}번: 필수 값 누락 {missing}")
        for key in ("path", "src", "dst", "pattern"):
            if key in step and not inside_sandbox(step[key]):
                errors.append(f"{i}번: 작업 폴더 밖 경로 '{step[key]}'")
        if action == "rename_prefix" and re.search(r"[\\/:*?\"<>|]", step.get("prefix", "")):
            errors.append(f"{i}번: 접두어에 사용할 수 없는 문자")
    return errors


# ------------------------------------------------------------------ 3. 미리보기 / 실행
def execute(plan, apply):
    changes = []
    for step in plan:
        a = step["action"]
        if a == "mkdir":
            target = SANDBOX / step["path"]
            if not target.exists():  # 멱등성: 이미 있으면 건너뜀
                changes.append(f"폴더 생성  {step['path']}/")
                apply and target.mkdir(parents=True)
        elif a == "move":
            for f in sorted(SANDBOX.glob(step["src"])):
                if f.is_file():
                    changes.append(f"이동      {f.relative_to(SANDBOX)} → {step['dst']}/{f.name}")
                    apply and shutil.move(f, SANDBOX / step["dst"] / f.name)
        elif a == "rename_prefix":
            files = set(SANDBOX.glob(step["pattern"]))
            if not apply:  # 미리보기에선 앞 단계의 이동이 아직 안 일어났으므로 이동될 파일도 포함
                files |= set(SANDBOX.glob(Path(step["pattern"]).name))
            for f in sorted(files):
                if f.is_file() and not f.name.startswith(step["prefix"]):
                    changes.append(f"이름 변경  {f.name} → {step['prefix']}{f.name}")
                    apply and f.rename(f.with_name(step["prefix"] + f.name))
    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("request", nargs="?", help="자연어 지시")
    parser.add_argument("--yes", action="store_true", help="미리보기 후 실제 실행")
    parser.add_argument("--plan", help="JSON 계획 파일을 직접 사용")
    parser.add_argument("--reset", action="store_true", help="연습 폴더 초기화")
    args = parser.parse_args()

    if args.reset or not SANDBOX.exists():
        reset_sandbox()
        if args.reset:
            return
    if args.plan:
        plan, source = json.loads(Path(args.plan).read_text(encoding="utf-8")), f"파일 {args.plan}"
    elif args.request:
        use_llm = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        plan = plan_with_llm(args.request) if use_llm else plan_with_rules(args.request)
        source = f"Gemini {MODEL}" if use_llm else "규칙 기반 파서(모의)"
    else:
        parser.error("자연어 지시 또는 --plan 이 필요합니다")

    steps = plan if isinstance(plan, list) else [plan]
    print(f"■ 계획 ({source})\n" + "\n".join(f"  {json.dumps(s, ensure_ascii=False)}" for s in steps) + "\n")
    errors = validate(plan)
    if errors:
        print("■ 검증 실패 — 실행하지 않습니다")
        print("\n".join(f"  ✘ {e}" for e in errors))
        return

    changes = execute(plan, apply=False)
    print("■ 미리보기 (dry-run)" if not args.yes else "■ 실행")
    print("\n".join(f"  {c}" for c in changes) or "  변경 사항 없음")
    if args.yes and changes:
        execute(plan, apply=True)
        with LOG.open("a", encoding="utf-8") as log:
            log.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {source}\n" + "".join(f"  {c}\n" for c in changes))
        print(f"\n완료. 로그: {LOG.name} / 현재 폴더: {sorted(str(p.relative_to(SANDBOX)) for p in SANDBOX.rglob('*'))}")
    elif changes:
        print("\n실제로 실행하려면 --yes 를 붙이세요.")


if __name__ == "__main__":
    main()
