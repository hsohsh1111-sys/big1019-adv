"""방문자 카운터 API — Redis가 있으면 Redis에, 없으면 메모리에 저장."""
import os
import socket

from fastapi import FastAPI

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
    return {"message": GREETING, "visits": incr(), "backend": backend,
            "version": APP_VERSION, "hostname": socket.gethostname()}  # hostname = 컨테이너/Pod 이름


@app.get("/health")
def health():
    return {"status": "ok"}
