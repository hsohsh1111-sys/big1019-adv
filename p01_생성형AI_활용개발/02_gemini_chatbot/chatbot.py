"""Gemini 대화형 챗봇 (무료 티어).

실행: python chatbot.py   (종료: quit)
GEMINI_API_KEY 가 없으면 모의 모드.
"""
import gemini_client

SYSTEM = "너는 친절한 프로그래밍 강사다. 초보자 눈높이로, 필요하면 짧은 예시 코드를 포함해 5줄 이내로 답한다."


def main():
    if gemini_client.has_key():
        from google import genai
        from google.genai import types

        chat = genai.Client().chats.create(
            model=gemini_client.MODEL, config=types.GenerateContentConfig(system_instruction=SYSTEM)
        )
        send = lambda text: chat.send_message(text).text  # noqa: E731
        mode = f"Gemini {gemini_client.MODEL}"
    else:
        memory = []

        def send(text):
            memory.append(text)
            return f"[모의 응답] 질문 {len(memory)}개를 기억 중입니다. 첫 질문은 '{memory[0]}' 이었어요."

        mode = "모의 모드 (GEMINI_API_KEY 없음)"

    print(f"=== 코딩 도우미 챗봇 ({mode}) ===  종료: quit")
    while True:
        try:
            text = input("나: ").strip()
        except EOFError:
            break
        if text.lower() in ("quit", "exit", "종료"):
            break
        if text:
            print("AI:", send(text))


if __name__ == "__main__":
    main()
