"""AI 메모장: FastAPI + SQLite + Gemini.

메모를 저장하면 AI가 요약·태그를 붙여 DB에 저장하고, 저장된 메모를 근거로 질문에 답한다(간단한 RAG).
실행: uvicorn app:app --reload  →  http://127.0.0.1:8000  (API 문서: /docs)
"""
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE = Path(__file__).parent
DB_PATH = Path(os.getenv("NOTES_DB", BASE / "notes.db"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

app = FastAPI(title="AI 메모장")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


with closing(db()) as conn:
    conn.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL, summary TEXT, tags TEXT, ai_source TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()


def has_key():
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def gemini(prompt, as_json=False):
    from google import genai
    from google.genai import types

    config = types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json" if as_json else None)
    return genai.Client().models.generate_content(model=MODEL, contents=prompt, config=config).text


def analyze(content):
    """AI로 요약·태그 생성. 실패하거나 키가 없으면 규칙 기반으로 대체(Fallback)."""
    if has_key():
        try:
            data = json.loads(gemini(
                '다음 메모를 분석해 JSON으로만 답하라. {"summary": "30자 이내 요약", "tags": ["태그", 최대 3개]}\n\n'
                + content, as_json=True))
            return str(data["summary"])[:100], [str(t).strip("# ")[:20] for t in data["tags"]][:3], "gemini"
        except Exception as e:  # AI 장애가 저장 실패로 이어지지 않게 한다
            print("AI 분석 실패, 규칙 기반으로 대체:", e)
    words = re.findall(r"[가-힣A-Za-z]{2,}", content)
    tags = sorted(set(words), key=lambda w: (-words.count(w), words.index(w)))[:3]
    return content[:30] + ("…" if len(content) > 30 else ""), tags, "mock"


class NoteIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=300)


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.post("/notes", status_code=201)
def create_note(note: NoteIn):
    summary, tags, source = analyze(note.content.strip())
    with closing(db()) as conn:
        cur = conn.execute("INSERT INTO notes (content, summary, tags, ai_source) VALUES (?, ?, ?, ?)",
                           (note.content.strip(), summary, ",".join(tags), source))
        conn.commit()
        return dict(conn.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone())


@app.get("/notes")
def list_notes(tag: str | None = None):
    with closing(db()) as conn:
        if tag:  # 파라미터 바인딩으로 SQL 인젝션 방지
            rows = conn.execute("SELECT * FROM notes WHERE tags LIKE ? ORDER BY id DESC", (f"%{tag}%",))
        else:
            rows = conn.execute("SELECT * FROM notes ORDER BY id DESC")
        return [dict(r) for r in rows]


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int):
    with closing(db()) as conn:
        if conn.execute("DELETE FROM notes WHERE id = ?", (note_id,)).rowcount == 0:
            raise HTTPException(404, "메모가 없습니다")
        conn.commit()


@app.post("/ask")
def ask(q: Question):
    """간단한 RAG: 질문 단어가 들어간 메모를 찾아 근거로 제공하고 답변을 생성."""
    words = re.findall(r"[가-힣A-Za-z0-9]{2,}", q.question)
    with closing(db()) as conn:
        notes = [dict(r) for r in conn.execute("SELECT id, content FROM notes ORDER BY id DESC LIMIT 200")]
    scored = sorted(((sum(w in n["content"] for w in words), n) for n in notes), key=lambda x: -x[0])
    related = [n for score, n in scored if score > 0][:3]
    if not related:
        return {"answer": "관련 메모를 찾지 못했습니다.", "sources": []}
    context = "\n".join(f"[메모 {n['id']}] {n['content']}" for n in related)
    if has_key():
        answer = gemini(f"다음 메모만 근거로 질문에 2문장 이내로 답하라.\n\n{context}\n\n질문: {q.question}")
    else:
        answer = f"[모의 답변] 관련 메모 {len(related)}개를 찾았습니다: " + related[0]["content"][:60]
    return {"answer": answer.strip(), "sources": [n["id"] for n in related]}
