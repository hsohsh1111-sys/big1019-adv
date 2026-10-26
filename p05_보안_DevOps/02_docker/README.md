# 02. Docker — 방문자 카운터 (FastAPI + Redis)

## 1. Docker 없이 먼저 실행 (메모리 저장)

```bash
pip install -r requirements.txt pytest httpx
uvicorn app.main:app --reload       # http://127.0.0.1:8000  → backend: "memory"
pytest -q
```

## 2. 컨테이너 하나로 실행

```bash
docker build -t visit-counter:v1 .
docker run --rm -p 8000:8000 -e GREETING="컨테이너에서 실행 중" visit-counter:v1
docker images visit-counter          # 이미지 크기 확인 (멀티 스테이지 빌드)
```

## 3. Docker Compose로 앱 + Redis 실행

```bash
docker compose up --build -d
curl http://localhost:8000           # 새로고침할 때마다 visits 증가, backend: "redis"
docker compose ps                    # 상태·헬스체크 확인
docker compose logs -f app           # 로그 보기
docker compose restart app           # 앱을 재시작해도 visits 유지 (Redis에 저장)
docker compose down                  # 종료 (볼륨 유지) / down -v : 데이터까지 삭제
```

## 파일별 포인트

| 파일 | 포인트 |
|---|---|
| `Dockerfile` | **멀티 스테이지 빌드**, non-root(`USER appuser`), `HEALTHCHECK` |
| `.dockerignore` | `.env`, `.git` 등이 이미지에 들어가지 않게 |
| `docker-compose.yml` | 서비스 이름으로 통신(`redis://redis:6379`), `depends_on` + 헬스체크, **볼륨**으로 데이터 유지, Redis 포트 비공개 |
| `app/main.py` | 설정을 **환경 변수**로 받음 → 같은 이미지를 개발·운영에서 재사용 |

## 보안 점검 (선택)

```bash
docker scout quickview visit-counter:v1       # Docker Desktop 내장 취약점 스캔
docker run --rm visit-counter:v1 whoami       # → appuser (root 아님 확인)
```
