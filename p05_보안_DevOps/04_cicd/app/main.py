"""CI/CD 실습용 간단한 API: 장바구니 금액 계산.

  /             : 브라우저 장바구니 화면
  /cart/total   : 금액 계산 API
  /health       : 헬스체크 + 배포된 버전 (CI가 넣어준 커밋 SHA)
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Cart API")

FREE_SHIPPING_THRESHOLD = 50_000
SHIPPING_FEE = 3_000
APP_VERSION = os.getenv("APP_VERSION", "local")  # Docker 빌드 시 --build-arg APP_VERSION=<커밋 SHA>


class Item(BaseModel):
    price: int = Field(ge=0)
    qty: int = Field(ge=1, le=99)


def total_price(items: list[Item]) -> int:
    subtotal = sum(i.price * i.qty for i in items)
    return subtotal if subtotal >= FREE_SHIPPING_THRESHOLD or subtotal == 0 else subtotal + SHIPPING_FEE


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/cart/total")
def cart_total(items: list[Item]):
    return {"total": total_price(items)}


@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}
