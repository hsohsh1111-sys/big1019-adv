"""LangChain용 Gemini 모델 생성. 키가 없으면 None을 돌려 각 예제가 가짜 모델을 쓰게 한다."""
import os

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


def gemini_or_none(temperature=0.3):
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=MODEL, google_api_key=key, temperature=temperature)
