from fastapi import FastAPI
from routers import item_router, user_router

app = FastAPI(title="모듈화된 FastAPI 프로젝트")

# 각 라우터를 메인 앱에 포함(Include) 시킵니다.
app.include_router(user_router.router)
app.include_router(item_router.router)


@app.get("/")
def root():
  return {"message": "서버가 정상적으로 동작 중입니다!"}