# 실행: uvicorn ex01_uvicorn:app --reload  →  http://127.0.0.1:8000/hello
import html

# fastapi 라이브러리에서 FastAPI 클래스를 가져온다.
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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


# 4. JSON 대신 HTML을 돌려주는 예시 ('/hello?name=이름') — 브라우저가 화면으로 그려준다
@app.get("/hello", response_class=HTMLResponse)
def hello(name: str = "방문자"):
  safe_name = html.escape(name)  # 사용자 입력을 HTML에 넣기 전에 특수문자 변환 (XSS 방지)
  return f"""
  <h1>안녕하세요, {safe_name}님!</h1>
  <form action="/hello"><input name="name" placeholder="이름"><button>인사하기</button></form>
  <ul>
    <li><a href="/">/ → JSON 응답</a></li>
    <li><a href="/items/5?q=hello">/items/5?q=hello → 경로 매개변수 + 쿼리 문자열</a></li>
    <li><a href="/items/abc">/items/abc → 타입 검증 실패(422)</a></li>
    <li><a href="/docs">/docs → 자동 생성된 API 문서 (Swagger UI)</a></li>
  </ul>
  """
