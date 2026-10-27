"""Gemini 대화형 챗봇 (무료 티어).

실행:
  uvicorn web:app --reload   # 브라우저 → http://127.0.0.1:8000
  python chatbot.py          # 터미널 (종료: quit)
GEMINI_API_KEY 가 없으면 모의 모드.
"""
import gemini_client

SYSTEM = "너는 친절한 프로그래밍 강사다. 초보자 눈높이로, 필요하면 짧은 예시 코드를 포함해 5줄 이내로 답한다."


def main():
    print(f"=== 코딩 도우미 챗봇 ({gemini_client.mode()}) ===  종료: quit")
    history = []
    while True:
        try:
            text = input("나: ").strip()
        except EOFError:
            break
        if text.lower() in ("quit", "exit", "종료"):
            break
        if not text:
            continue
        history.append({"role": "user", "content": text})
        answer = gemini_client.chat(history, system=SYSTEM)
        history.append({"role": "assistant", "content": answer})
        print("AI:", answer)


if __name__ == "__main__":
    main()
