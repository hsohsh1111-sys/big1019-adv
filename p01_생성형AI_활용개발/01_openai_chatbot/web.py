"""브라우저용 고객센터 챗봇 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import chatbot

app = FastAPI(title="OpenAI 고객센터 챗봇")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatIn(BaseModel):
    history: list[Message] = Field(min_length=1, max_length=50)  # 너무 긴 대화는 비용 폭증 → 제한


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/api/mode")
def get_mode():
    return {"mode": chatbot.mode()}


@app.post("/api/chat")
def chat(body: ChatIn):
    answer, usage = chatbot.ask([m.model_dump() for m in body.history])
    return {"answer": answer, "usage": usage}
