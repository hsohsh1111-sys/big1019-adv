# 실행: uvicorn ex02_sqlalchemy:app --reload  →  http://127.0.0.1:8000
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv  # find_dotenv 추가
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from typing import Annotated

# 1. 상위 폴더를 탐색하여 프로젝트 루트의 .env 파일을 자동으로 찾아 로드합니다.
load_dotenv(find_dotenv())

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")

# 환경변수가 잘 들어왔는지 확인용 프린트 (나중에 삭제해도 무방)
print(f"디버그 - 연결할 호스트: {DB_HOST}, 데이터베이스: {DB_DATABASE}")

if DB_HOST:  # .env 에 TiDB/MySQL 정보가 있으면 원격 DB 사용
  DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
else:  # 없으면 이 폴더의 SQLite 파일로 연습 (설치·가입 불필요)
  DATABASE_URL = f"sqlite:///{(Path(__file__).parent / 'users.db').as_posix()}"

# 만약 ssl_ca=None으로도 에러가 난다면 아래처럼 처리할 수 있습니다:
# DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
# engine = create_engine(DATABASE_URL, connect_args={'ssl': {'ssl_mode': 'PREFERRED'}})

# MySQL/TiDB 데이터베이스와 파이썬을 연결하는 엔진 생성
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 2. DB 모델(테이블) 정의 - User 클래스가 MySQL의 'users' 테이블이 됩니다.
class UserModel(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(50), nullable=False)
  email = Column(String(100), unique=True, index=True)


# 데이터베이스 내에 users 테이블이 없다면 자동으로 생성
Base.metadata.create_all(bind=engine)

app = FastAPI()


# 3. 데이터베이스 세션(연결 통로)을 가져오는 의존성 함수
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()  # 요청이 끝나면 반드시 연결을 닫아줍니다.


# 브라우저 화면 (index.html 이 아래 API를 fetch로 호출)
@app.get("/")
def index():
  return FileResponse(Path(__file__).parent / "index.html")


# 4. 유저 생성 API (Create)
DbSession = Annotated[Session, Depends(get_db)]

@app.post("/users/", responses={400: {"descripton:": "이미 등록된 이메일입니다."}})
def create_user(name: str, email: str, db: DbSession):
  # 새로운 유저 객체 생성
  db_user = UserModel(name=name, email=email)
  db.add(db_user)  # DB에 추가 준비
  try:
    db.commit()  # DB에 최종 반영 (저장)
  except IntegrityError:  # email 은 unique → 같은 이메일로 두 번 저장하면 오류
    db.rollback()
    raise HTTPException(400, "이미 등록된 이메일입니다.") from None
  db.refresh(db_user)  # 생성된 데이터(id 등) 새로고침
  return {"message": "유저가 성공적으로 생성되었습니다!", "user": db_user}


# 5. 유저 목록 조회 API (Read)
@app.get("/users/")
def get_users(db: DbSession):
  # SQL의 SELECT * FROM users 와 동일한 역할
  users = db.query(UserModel).all()
  return users
