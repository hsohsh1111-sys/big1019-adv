"""OpenAI API 대화형 챗봇 (유료).

OPENAI_API_KEY 가 없으면 모의(mock) 모드로 동작해 무료로 흐름을 익힐 수 있다.
실행: python chatbot.py   (종료: quit)
"""
import os

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
INSTRUCTIONS = "너는 온라인 쇼핑몰 고객센터 상담원이다. 3문장 이내로 친절하게 답한다."


def ask_openai(history):
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(model=MODEL, instructions=INSTRUCTIONS, input=history)
    usage = response.usage
    print(f"   (토큰: 입력 {usage.input_tokens} / 출력 {usage.output_tokens})")
    return response.output_text


def ask_mock(history):
    question = history[-1]["content"]
    turns = sum(1 for m in history if m["role"] == "user")
    return f"[모의 응답 #{turns}] '{question}'에 대한 답변입니다. 지금까지 질문 {turns}개를 기억하고 있어요."


def main():
    ask = ask_openai if os.getenv("OPENAI_API_KEY") else ask_mock
    print(f"=== 고객센터 챗봇 ({'OpenAI ' + MODEL if ask is ask_openai else '모의 모드'}) ===  종료: quit")
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
        answer = ask(history)
        history.append({"role": "assistant", "content": answer})
        print("AI:", answer)


if __name__ == "__main__":
    main()
