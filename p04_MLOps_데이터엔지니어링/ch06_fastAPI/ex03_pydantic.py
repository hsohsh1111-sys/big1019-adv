from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field


# 1. Pydantic을 이용한 데이터 스키마(요청 데이터 구조) 정의
class ItemSchema(BaseModel):
  name: str = Field(..., min_length=2, description="상품 이름은 최소 2글자 이상이어야 합니다.")
  description: Optional[str] = Field(None, max_length=300, description="상품 설명 (선택)")
  price: float = Field(..., gt=0, description="상품 가격은 0보다 커야 합니다.")
  tax: Optional[float] = None


app = FastAPI()


# 2. POST 요청에서 Pydantic 스키마를 매개변수로 사용
@app.post("/items/")
def create_item(item: ItemSchema):
  # item 변수는 이미 Pydantic에 의해 완벽하게 검증된 안전한 객체입니다.
  return {
      "message": "상품이 성공적으로 등록되었습니다!",
      "data": {
          "name": item.name,
          "price": item.price,
          "total_price": item.price + (item.tax if item.tax else 0),
      },
  }