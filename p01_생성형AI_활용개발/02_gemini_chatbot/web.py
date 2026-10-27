"""브라우저용 Gemini 챗봇 + FAQ 자동 응답 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import auto_reply
import chatbot
import gemini_client

app = FastAPI(title="Gemini 챗봇 & 자동 응답")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatIn(BaseModel):
    history: list[Message] = Field(min_length=1, max_length=50)


class Inquiry(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/api/info")
def info():
    return {"mode": gemini_client.mode(), "faq": auto_reply.FAQ, "samples": auto_reply.SAMPLES}


@app.post("/api/chat")
def chat(body: ChatIn):
    return {"answer": gemini_client.chat([m.model_dump() for m in body.history], system=chatbot.SYSTEM)}


@app.post("/api/reply")
def reply(body: Inquiry):
    source, masked, answer = auto_reply.reply(body.question)
    return {"source": source, "masked": masked, "answer": answer}
