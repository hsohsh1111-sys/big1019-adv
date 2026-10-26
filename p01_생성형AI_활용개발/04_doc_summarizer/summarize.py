"""회의록 요약 + 보고서(Markdown) 자동 생성.

- 키가 있으면: Gemini 생성 요약 + JSON 구조화 추출 (긴 문서는 Map-Reduce)
- 키가 없으면: 단어 빈도 기반 추출 요약 + 정규식 추출 (완전 무료·오프라인)

실행: python summarize.py sample_meeting.txt
결과: output/summary.txt, output/report.md
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
CHUNK_CHARS = 3000
OUT = Path(__file__).parent / "output"


# ---------------------------------------------------------------- LLM 방식
def gemini(prompt, as_json=False):
    from google import genai
    from google.genai import types

    config = types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json" if as_json else None)
    return genai.Client().models.generate_content(model=MODEL, contents=prompt, config=config).text


def chunks(text, size=CHUNK_CHARS):
    paras, buf = text.split("\n\n"), ""
    for p in paras:
        if len(buf) + len(p) > size and buf:
            yield buf
            buf = ""
        buf += p + "\n\n"
    if buf.strip():
        yield buf


def llm_summary(text):
    parts = list(chunks(text))
    if len(parts) > 1:  # Map: 조각별 요약 → Reduce: 합쳐서 다시 요약
        text = "\n".join(gemini(f"다음 글을 5줄 이내로 요약:\n{p}") for p in parts)
    return gemini(f"다음 회의록을 핵심 결정사항 중심으로 3줄 요약하라. 원문에 없는 내용은 쓰지 마라.\n\n{text}")


def llm_extract(text):
    prompt = (
        "회의록에서 정보를 추출해 아래 JSON 스키마로만 답하라.\n"
        '{"title": str, "date": str, "attendees": [str], "decisions": [str],'
        ' "todos": [{"owner": str, "task": str, "due": str}], "next_meeting": str}\n\n' + text
    )
    return json.loads(gemini(prompt, as_json=True))


# ---------------------------------------------------------------- 무료 오프라인 방식
STOPWORDS = {"있다", "했다", "한다", "하기로", "위해", "같은", "먼저", "이", "그", "및", "총", "중"}


def extractive_summary(text, n=3):
    sentences = [s.strip() for s in re.split(r"(?<=[.다])\s+|\n", text) if len(s.strip()) > 15]
    words = lambda s: [w for w in re.findall(r"[가-힣A-Za-z]{2,}", s) if w not in STOPWORDS]  # noqa: E731
    freq = Counter(w for s in sentences for w in words(s))
    scored = sorted(sentences, key=lambda s: sum(freq[w] for w in words(s)) / (len(words(s)) or 1), reverse=True)
    top = set(scored[:n])
    return "\n".join(f"- {s}" for s in sentences if s in top)


def regex_extract(text):
    header = re.search(r"\[(.+?)\]\s*([\d-]+).*?참석:\s*(.+)", text)
    todos = [{"owner": o, "due": d, "task": t.strip()}
             for o, d, t in re.findall(r"([가-힣]{2,4})(?:은|는)\s*(\d+월\s*\d+일)까지\s*(.+?)\.", text)]
    next_m = re.search(r"다음 회의\s*\n(.+)", text)
    return {
        "title": header.group(1) if header else "회의록",
        "date": header.group(2) if header else "",
        "attendees": [a.strip() for a in header.group(3).split(",")] if header else [],
        "decisions": [s.strip() + "." for s in re.findall(r"([^.\n]*결정[^.\n]*)\.", text)],
        "todos": todos,
        "next_meeting": next_m.group(1).strip() if next_m else "",
    }


# ---------------------------------------------------------------- 보고서 템플릿
def render_report(info, summary, mode):
    lines = [f"# {info['title']} 요약 보고서", "",
             f"- 일시: {info['date']}", f"- 참석: {', '.join(info['attendees'])}", f"- 생성 방식: {mode}", "",
             "## 요약", summary.strip(), "", "## 결정사항"]
    lines += [f"{i}. {d}" for i, d in enumerate(info["decisions"], 1)] or ["- 없음"]
    lines += ["", "## 할 일", "", "| 담당 | 할 일 | 기한 |", "|---|---|---|"]
    lines += [f"| {t['owner']} | {t['task']} | {t['due']} |" for t in info["todos"]]
    lines += ["", "## 다음 회의", info["next_meeting"] or "미정", ""]
    return "\n".join(lines)


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "sample_meeting.txt")
    text = src.read_text(encoding="utf-8")
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        mode, summary, info = f"Gemini ({MODEL})", llm_summary(text), llm_extract(text)
    else:
        mode, summary, info = "추출 요약 (오프라인)", extractive_summary(text), regex_extract(text)

    missing = [k for k in ("title", "decisions", "todos") if not info.get(k)]
    if missing:
        print("⚠ 추출되지 않은 항목:", missing)

    OUT.mkdir(exist_ok=True)
    (OUT / "summary.txt").write_text(summary, encoding="utf-8")
    report = render_report(info, summary, mode)
    (OUT / "report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\n저장 완료: {OUT / 'summary.txt'}, {OUT / 'report.md'}")


if __name__ == "__main__":
    main()
