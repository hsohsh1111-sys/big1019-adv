from fastapi import APIRouter

# APIRouter 인스턴스 생성 (prefix로 공통 주소 지정 가능)
router = APIRouter(prefix="/users", tags=["Users (유저 관리)"])


@router.get("/")
def get_users():
  return [{"username": "김해원"}, {"username": "황상옥"}]


@router.post("/")
def create_user(name: str):
  return {"message": f"유저 '{name}' 생성 완료!"}