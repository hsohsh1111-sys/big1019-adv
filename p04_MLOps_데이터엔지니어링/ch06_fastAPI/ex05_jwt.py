from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

# 설정 정보 (실제 서비스에서는 환경변수로 관리해야 합니다)
SECRET_KEY = "my_super_secret_key_change_it_frequently"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 토큰 유효 시간 (30분)


# 비밀번호 암호화를 위한 설정 (bcrypt 사용)
def hash_password(password: str) -> str:
  return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
  return bcrypt.checkpw(password.encode(), hashed_password.encode())


# OAuth2 인증 스키마 설정 (로그인 요청을 보낼 경로 지정)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

# 가상의 회원 데이터베이스 (실제로는 MySQL/TiDB 등의 DB 사용)
fake_users_db = {
    "haewon": {
        "username": "haewon",
        "email": "haewon@example.com",
        # 'password123'을 해싱한 값
        "hashed_password": hash_password("password123"),
    }
}


# 토큰 응답 스키마
class Token(BaseModel):
  access_token: str
  token_type: str


# 1. 로그인 및 JWT 토큰 발급 API
@app.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
  # 유저 존재 여부 확인
  user = fake_users_db.get(form_data.username)
  if not user or not verify_password(form_data.password, user["hashed_password"]):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

  # 토큰 만료 시간 계산
  expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  to_encode = {"sub": user["username"], "exp": expire}

  # JWT 토큰 생성
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

  return {"access_token": encoded_jwt, "token_type": "bearer"}


# 2. 인증이 필요한 보호된 엔드포인트 (내 정보 조회)
@app.get("/users/me")
def read_users_me(token: str = Depends(oauth2_scheme)):
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="자격 증명을 확인할 수 없습니다.",
      headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    # 토큰 해독 및 유효성 검사
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      raise credentials_exception
  except JWTError:
    raise credentials_exception

  return {"username": username, "message": "인증에 성공한 안전한 API 데이터입니다!"}