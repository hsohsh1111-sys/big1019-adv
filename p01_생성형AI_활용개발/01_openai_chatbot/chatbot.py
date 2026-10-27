"""OpenAI API 대화형 챗봇 (유료).

OPENAI_API_KEY 가 없으면 모의(mock) 모드로 동작해 무료로 흐름을 익힐 수 있다.
실행:
  uvicorn web:app --reload   # 브라우저 챗봇 → http://127.0.0.1:8000
  python chatbot.py          # 터미널 챗봇 (종료: quit)
"""
import os

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
INSTRUCTIONS = "너는 온라인 쇼핑몰 고객센터 상담원이다. 3문장 이내로 친절하게 답한다."


def has_key():
    return bool(os.getenv("OPENAI_API_KEY"))


def mode():
    return f"OpenAI {MODEL}" if has_key() else "모의 모드 (OPENAI_API_KEY 없음)"


def ask_openai(history):
    from openai import OpenAI

    response = OpenAI().responses.create(model=MODEL, instructions=INSTRUCTIONS, input=history)
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return response.output_text, usage


def ask_mock(history):
    question = history[-1]["content"]
    turns = sum(1 for m in history if m["role"] == "user")
    answer = f"[모의 응답 #{turns}] '{question}'에 대한 답변입니다. 지금까지 질문 {turns}개를 기억하고 있어요."
    # 실제 토큰 대신 글자 수로 흉내: 대화가 길어질수록 입력이 커지는 것을 확인하는 용도
    usage = {"input_tokens": sum(len(m["content"]) for m in history), "output_tokens": len(answer)}
    return answer, usage


def ask(history):
    """대화 기록 전체를 보내고 (답변, 토큰 사용량)을 받는다.

    LLM API는 이전 대화를 기억하지 못한다(stateless). 그래서 매번 history 전체를 다시 보낸다.
    """
    return ask_openai(history) if has_key() else ask_mock(history)


def main():
    print(f"=== 고객센터 챗봇 ({mode()}) ===  종료: quit")
    history = []
    while True:
        try:
            question = input("나: ").strip()
        except EOFError:
            break
        if question.lower() in ("quit", "exit", "종료"):
            break
        if not question:
            continue
        history.append({"role": "user", "content": question})
        answer, usage = ask(history)
        history.append({"role": "assistant", "content": answer})
        print("AI:", answer)
        print(f"   (토큰: 입력 {usage['input_tokens']} / 출력 {usage['output_tokens']})")


if __name__ == "__main__":
    main()
