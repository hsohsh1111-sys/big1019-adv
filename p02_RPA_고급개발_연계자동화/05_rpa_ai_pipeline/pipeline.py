"""RPA + AI 파이프라인: 수집(RPA) → 분류·요약(AI) → 사람 검토 분기 → 엑셀 보고서 + 알림 메일 초안.

대상: 연습용 명언 사이트 quotes.toscrape.com
실행: python pipeline.py --pages 2
GEMINI_API_KEY 가 있으면 Gemini가 분류, 없으면 태그·키워드 규칙으로 분류(모의).
"""
import argparse
import json
import os
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = "https://quotes.toscrape.com/page/{}/"
OUT = Path(__file__).parent / "output"
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
THEMES = ["사랑", "인생", "성공", "유머", "지혜", "기타"]
REVIEW_THRESHOLD = 0.6


# ---------------------------------------------------------------- 1. RPA: 수집
def collect(pages, delay=1.0):
    items = []
    for page in range(1, pages + 1):
        res = requests.get(URL.format(page), timeout=10, headers={"User-Agent": "edu-practice"})
        res.raise_for_status()
        for q in BeautifulSoup(res.text, "html.parser").select("div.quote"):
            items.append({
                "id": len(items) + 1,
                "text": q.select_one("span.text").text.strip("“”"),
                "author": q.select_one("small.author").text,
                "tags": [t.text for t in q.select("a.tag")],
            })
        print(f"[수집] {page}페이지 누적 {len(items)}건")
        time.sleep(delay)
    return items


# ---------------------------------------------------------------- 2. AI: 분류
def classify_with_gemini(items):
    from google import genai
    from google.genai import types

    client = genai.Client()
    results = []
    for start in range(0, len(items), 10):  # 10건씩 묶어서 요청 → 호출 수 절감
        batch = [{"id": i["id"], "text": i["text"], "tags": i["tags"]} for i in items[start:start + 10]]
        prompt = (f"각 명언을 분석해 JSON 배열로만 답하라. 항목: id, theme({'|'.join(THEMES)}), "
                  "sentiment(긍정|부정|중립), confidence(0~1 확신도), summary_ko(15자 이내 한국어 요약)\n"
                  + json.dumps(batch, ensure_ascii=False))
        text = client.models.generate_content(
            model=MODEL, contents=prompt,
            config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json")).text
        results += json.loads(text)
        time.sleep(1)
    return {r["id"]: r for r in results}


RULES = {"사랑": ["love", "romance", "heart"], "유머": ["humor", "funny"], "성공": ["success", "inspirational", "dreams"],
         "인생": ["life", "live", "living"], "지혜": ["wisdom", "truth", "knowledge", "books", "mind"]}
NEGATIVE = ["never", "fear", "death", "lie", "hate", "fail"]


def classify_with_rules(items):
    results = {}
    for i in items:
        words = set(i["tags"]) | set(i["text"].lower().replace(",", " ").replace(".", " ").split())
        theme = next((t for t, kws in RULES.items() if words & set(kws)), "기타")
        results[i["id"]] = {
            "theme": theme,
            "sentiment": "부정" if words & set(NEGATIVE) else "긍정",
            "confidence": 0.9 if set(i["tags"]) & {k for kws in RULES.values() for k in kws} else 0.4,
            "summary_ko": f"[모의] {i['author']}의 {theme} 명언",
        }
    return results


# ---------------------------------------------------------------- 3. 보고
def report(df, mode):
    OUT.mkdir(exist_ok=True)
    review = df[(df["확신도"] < REVIEW_THRESHOLD) | (~df["주제"].isin(THEMES))]
    stats = df.groupby("주제").agg(건수=("id", "count"), 긍정비율=("감정", lambda s: round((s == "긍정").mean(), 2)))
    xlsx = OUT / "quotes_report.xlsx"
    with pd.ExcelWriter(xlsx) as w:
        df.to_excel(w, sheet_name="전체", index=False)
        stats.to_excel(w, sheet_name="주제별 통계")
        review.to_excel(w, sheet_name="검토 필요", index=False)

    msg = EmailMessage()  # 알림 메일 초안 (.eml) — 04 예제의 SMTP 코드로 실제 발송 가능
    msg["From"], msg["To"] = "rpa-bot@example.com", "team@example.com"
    msg["Subject"] = f"[RPA 보고] 명언 {len(df)}건 분석 완료 ({datetime.now():%m/%d %H:%M})"
    msg.set_content(f"분석 방식: {mode}\n\n[주제별 건수]\n{stats.to_string()}\n\n"
                    f"사람 검토 필요: {len(review)}건 (확신도 {REVIEW_THRESHOLD} 미만)\n첨부 보고서를 확인하세요.")
    msg.add_attachment(xlsx.read_bytes(), maintype="application", subtype="octet-stream", filename=xlsx.name)
    (OUT / "notify.eml").write_bytes(bytes(msg))
    return stats, review


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=2)
    args = parser.parse_args()

    items = collect(args.pages)
    use_ai = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    mode = f"Gemini {MODEL}" if use_ai else "규칙 기반(모의)"
    try:
        analysis = classify_with_gemini(items) if use_ai else classify_with_rules(items)
    except Exception as e:  # AI 장애 시 규칙으로 대체하고 표시
        print("AI 분류 실패 → 규칙 기반으로 대체:", e)
        analysis, mode = classify_with_rules(items), "규칙 기반(AI 장애 대체)"
    print(f"[분류] {mode} 완료")

    df = pd.DataFrame([{
        "id": i["id"], "명언": i["text"], "저자": i["author"], "태그": ", ".join(i["tags"]),
        "주제": analysis.get(i["id"], {}).get("theme", "기타"),
        "감정": analysis.get(i["id"], {}).get("sentiment", "중립"),
        "확신도": float(analysis.get(i["id"], {}).get("confidence", 0)),
        "요약": analysis.get(i["id"], {}).get("summary_ko", ""),
    } for i in items])
    stats, review = report(df, mode)
    print(f"\n{stats}\n\n사람 검토 필요 {len(review)}건 → {OUT / 'quotes_report.xlsx'} ('검토 필요' 시트)")
    print(f"알림 메일 초안 → {OUT / 'notify.eml'}")


if __name__ == "__main__":
    main()
