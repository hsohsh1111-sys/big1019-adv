"""내 PC에서만 동작하는 테스트 메일 서버 (실제 발송 X).

받은 메일을 inbox/ 폴더에 .eml 파일로 저장한다. .eml 은 Outlook·Thunderbird 또는 메모장으로 열 수 있다.
실행: python mail_server.py   (종료: Ctrl+C)
"""
import time
from datetime import datetime
from email import message_from_bytes, policy
from pathlib import Path

from aiosmtpd.controller import Controller

HOST, PORT = "127.0.0.1", 1025
INBOX = Path(__file__).parent / "inbox"


class SaveToInbox:
    async def handle_DATA(self, server, session, envelope):
        INBOX.mkdir(exist_ok=True)
        msg = message_from_bytes(envelope.content, policy=policy.default)
        path = INBOX / f"{datetime.now():%H%M%S_%f}.eml"
        path.write_bytes(envelope.content)
        attachments = [p.get_filename() for p in msg.iter_attachments()]
        print(f"📨 {', '.join(envelope.rcpt_tos)} | {msg['Subject']} | 첨부 {attachments} → {path.name}")
        return "250 OK"


def start():
    controller = Controller(SaveToInbox(), hostname=HOST, port=PORT)
    controller.start()
    return controller


if __name__ == "__main__":
    server = start()
    print(f"테스트 메일 서버 실행 중: {HOST}:{PORT}  (받은 메일 → {INBOX})  종료: Ctrl+C")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
