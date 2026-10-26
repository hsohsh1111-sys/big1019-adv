"""Gemini 호출 공통 모듈. GEMINI_API_KEY 가 없으면 모의 응답을 돌려준다."""
import os
import time

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


def has_key():
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def ask(prompt, system=None, temperature=0.5, retries=3):
    """프롬프트 한 번 보내고 텍스트 답변을 받는다. 429(한도 초과)면 잠시 기다렸다 재시도."""
    if not has_key():
        return f"[모의 응답] {prompt.strip().splitlines()[-1][:60]} ... 에 대한 AI 답변이 여기에 표시됩니다."

    from google import genai
    from google.genai import errors, types

    client = genai.Client()
    config = types.GenerateContentConfig(system_instruction=system, temperature=temperature)
    for attempt in range(retries):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt, config=config).text
        except errors.APIError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = 2 ** (attempt + 2)
                print(f"   (요청 한도 초과, {wait}초 후 재시도)")
                time.sleep(wait)
            else:
                raise
