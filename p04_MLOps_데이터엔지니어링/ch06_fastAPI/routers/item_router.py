from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["Items (상품 관리)"])


@router.get("/")
def get_items():
  return [{"item_name": "노트북"}, {"item_name": "키보드"}]