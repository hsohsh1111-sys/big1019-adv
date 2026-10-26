# fastapi 라이브러리에서 FastAPI 클래스를 가져온다.
from fastapi import FastAPI

# 1. FastAPI 앱 인스턴스 생성
app = FastAPI()


# 2. 루트 경로('/')로 GET 요청이 올 때 실행될 함수 정의
@app.get("/")
def read_root():
  return {"message": "안녕하세요! FastAPI 서버가 정상적으로 실행되었습니다."}


# 3. 매개변수를 받는 예시 경로 ('/items/원하는숫자')
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
  return {"item_id": item_id, "query_string": q}