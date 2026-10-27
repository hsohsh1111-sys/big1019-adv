"""방문자 카운터 — Redis가 있으면 Redis에, 없으면 메모리에 저장.

  /           : 브라우저 화면 (index.html)
  /api/visit  : 방문 수 +1 후 JSON 반환 (curl 용)
  /health     : 헬스체크 (Docker HEALTHCHECK, Kubernetes 프로브)
"""
import os
import socket
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse

app = FastAPI(title="Visit Counter")
APP_VERSION = os.getenv("APP_VERSION", "v1")
GREETING = os.getenv("GREETING", "안녕하세요")
REDIS_URL = os.getenv("REDIS_URL")  # 예: redis://redis:6379/0  (docker compose 서비스 이름으로 접속)

if REDIS_URL:
    import redis

    store = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    incr = lambda: store.incr("visits")  # noqa: E731
    backend = "redis"
else:
    _count = {"visits": 0}

    def incr():
        _count["visits"] += 1
        return _count["visits"]

    backend = "memory"


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/api/visit")
def visit(response: Response):
    # 요청마다 연결을 끊어 다음 요청이 새 연결이 되게 함 → 쿠버네티스에서 여러 Pod로 분산되는 모습이 보임
    response.headers["Connection"] = "close"
    return {"message": GREETING, "visits": incr(), "backend": backend,
            "version": APP_VERSION, "hostname": socket.gethostname()}  # hostname = 컨테이너/Pod 이름


@app.get("/health")
def health():
    return {"status": "ok"}
