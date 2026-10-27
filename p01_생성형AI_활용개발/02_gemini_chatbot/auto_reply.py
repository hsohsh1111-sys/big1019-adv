"""FAQ + Gemini 자동 응답 시스템.

1) 개인정보 마스킹 → 2) FAQ 키워드 매칭(무료·즉시) → 3) 없으면 Gemini가 FAQ를 근거로 답변
→ 4) 답변 검증(길이·금지어) → 실패 시 상담원 연결

실행:
  uvicorn web:app --reload      # 브라우저 → http://127.0.0.1:8000
  python auto_reply.py          # 샘플 문의 일괄 처리
  python auto_reply.py -i       # 직접 입력
"""
import json
import re
import sys
from pathlib import Path

import gemini_client

FAQ = json.loads((Path(__file__).parent / "faq.json").read_text(encoding="utf-8"))
BANNED = ["주민등록번호", "비밀번호", "카드번호"]
HANDOFF = "정확한 안내를 위해 상담원에게 연결해 드릴게요. (평일 09:00~18:00)"

SAMPLES = [
    "환불은 어떻게 하나요?",
    "주문한 거 언제 와요? 제 번호는 010-1234-5678 이에요",
    "선물 포장도 해주시나요?",
    "회원 탈퇴하면 적립금은 어떻게 되나요?",
]


def mask_pii(text):
    text = re.sub(r"01[016789]-?\d{3,4}-?\d{4}", "[전화번호]", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[이메일]", text)
    return re.sub(r"\d{6}-?[1-4]\d{6}", "[주민번호]", text)


def match_faq(question):
    for item in FAQ:
        if any(k in question for k in item["keywords"]):
            return item["answer"]
    return None


def ask_ai(question):
    faq_text = "\n".join(f"- {', '.join(i['keywords'])}: {i['answer']}" for i in FAQ)
    prompt = (
        "다음 FAQ만 근거로 고객 질문에 2문장 이내로 답하라. "
        f'FAQ로 답할 수 없으면 정확히 "{HANDOFF}" 라고만 답하라.\n\n[FAQ]\n{faq_text}\n\n[고객 질문]\n{question}'
    )
    if not gemini_client.has_key():
        return HANDOFF if "탈퇴" in question else f"[모의 AI 답변] '{question}' 관련 안내입니다."
    return gemini_client.ask(prompt, system="너는 쇼핑몰 고객센터 상담원이다.", temperature=0.2).strip()


def validate(answer):
    return 0 < len(answer) <= 300 and not any(b in answer for b in BANNED)


def reply(raw_question):
    question = mask_pii(raw_question)
    if answer := match_faq(question):
        return "FAQ", question, answer
    answer = ask_ai(question)
    if not validate(answer):
        return "상담원", question, HANDOFF
    return ("상담원" if answer == HANDOFF else "AI"), question, answer


def main():
    print(f"[자동 응답 시스템] AI 모드: {gemini_client.mode()}\n")
    questions = iter(lambda: input("문의: ").strip(), "") if "-i" in sys.argv else SAMPLES
    for q in questions:
        source, masked, answer = reply(q)
        print(f"문의: {q}")
        if masked != q:
            print(f"  ↳ 마스킹: {masked}")
        print(f"  [{source}] {answer}\n")


if __name__ == "__main__":
    main()
