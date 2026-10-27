"""Gemini 호출 공통 모듈. GEMINI_API_KEY 가 없으면 모의 응답을 돌려준다."""
import os
import time

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


def has_key():
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def mode():
    return f"Gemini {MODEL}" if has_key() else "모의 모드 (GEMINI_API_KEY 없음)"


def _generate(contents, system, temperature, retries=3):
    """실제 Gemini 호출. 429(무료 한도 초과)면 잠시 기다렸다 재시도."""
    from google import genai
    from google.genai import errors, types

    client = genai.Client()
    config = types.GenerateContentConfig(system_instruction=system, temperature=temperature)
    for attempt in range(retries):
        try:
            return client.models.generate_content(model=MODEL, contents=contents, config=config).text
        except errors.APIError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = 2 ** (attempt + 2)
                print(f"   (요청 한도 초과, {wait}초 후 재시도)")
                time.sleep(wait)
            else:
                raise


def ask(prompt, system=None, temperature=0.5):
    """단발성 질문: 프롬프트 한 번 보내고 텍스트 답변을 받는다."""
    if not has_key():
        return f"[모의 응답] {prompt.strip().splitlines()[-1][:60]} ... 에 대한 AI 답변이 여기에 표시됩니다."
    return _generate(prompt, system, temperature)


def chat(history, system=None, temperature=0.7):
    """대화형: history = [{"role": "user"|"assistant", "content": "..."}] 전체를 보낸다.

    Gemini는 assistant 대신 "model" 이라는 role 이름을 쓰므로 변환해서 보낸다.
    """
    if not has_key():
        questions = [m["content"] for m in history if m["role"] == "user"]
        return f"[모의 응답] 질문 {len(questions)}개를 기억 중입니다. 첫 질문은 '{questions[0]}' 이었어요."
    contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in history]
    return _generate(contents, system, temperature)
