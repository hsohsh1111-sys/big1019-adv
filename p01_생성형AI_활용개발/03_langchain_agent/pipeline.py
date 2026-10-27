"""LCEL 파이프라인: 긴 글 → (1) 3줄 요약 → (2) 요약으로 제목 생성 → (3) 결과 dict.

실행:
  uvicorn web:app --reload   # 브라우저 → http://127.0.0.1:8000
  python pipeline.py         # 터미널
키가 없으면 FakeListChatModel(정해진 답을 순서대로 돌려주는 가짜 LLM)으로 동작.
"""
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from llm import gemini_or_none

ARTICLE = """
최근 많은 기업이 반복적인 사무 업무를 자동화하기 위해 RPA와 생성형 AI를 함께 도입하고 있다.
RPA는 정해진 규칙에 따라 화면 클릭, 데이터 입력 같은 작업을 사람 대신 수행한다.
생성형 AI는 이메일 분류, 문서 요약처럼 규칙으로 정하기 어려운 판단을 돕는다.
두 기술을 결합하면 송장 처리 시간이 70% 이상 줄었다는 사례도 보고되었다.
다만 AI의 판단 오류에 대비해 사람이 최종 확인하는 절차가 필요하다는 지적도 있다.
"""

llm = gemini_or_none() or FakeListChatModel(responses=[
    "1. 기업들이 RPA와 생성형 AI를 함께 도입하고 있다.\n"
    "2. RPA는 규칙 작업, AI는 판단 작업을 맡는다.\n"
    "3. 효과가 크지만 사람의 최종 확인이 필요하다.",
    "RPA와 생성형 AI의 만남, 업무 자동화의 새 기준",
])

summarize_prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 신문 편집자다. 핵심만 번호 목록 3줄로 요약한다."),
    ("human", "다음 기사를 요약해줘:\n{article}"),
])
title_prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 카피라이터다. 25자 이내 제목 하나만 출력한다."),
    ("human", "다음 요약에 어울리는 제목:\n{summary}"),
])

summary_chain = summarize_prompt | llm | StrOutputParser()
title_chain = title_prompt | llm | StrOutputParser()

# {"article"} → +summary → +title : 앞 단계 결과가 dict에 누적되며 다음 단계로 전달된다
pipeline = RunnablePassthrough.assign(summary=summary_chain) | RunnablePassthrough.assign(title=title_chain)


def run_pipeline(article):
    result = pipeline.invoke({"article": article})
    return {"model": type(llm).__name__, "title": result["title"].strip(), "summary": result["summary"].strip()}


if __name__ == "__main__":
    out = run_pipeline(ARTICLE)
    print(f"[모델] {out['model']}\n")
    print("■ 제목:", out["title"])
    print("■ 요약:\n" + out["summary"])
