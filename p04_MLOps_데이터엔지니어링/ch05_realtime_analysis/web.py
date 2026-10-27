"""실시간 이상 탐지 대시보드 서버 — Server-Sent Events(SSE)로 판정 결과를 브라우저에 밀어준다.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse

import stream_monitor

app = FastAPI(title="실시간 이상 탐지")


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/stream")
def stream(seconds: int = Query(30, ge=5, le=120)):
    def events():
        consumer = stream_monitor.Consumer()
        for event in stream_monitor.stream(seconds, consumer):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"  # SSE 형식: "data: ...\n\n"
        yield f"event: summary\ndata: {json.dumps(consumer.summary())}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
