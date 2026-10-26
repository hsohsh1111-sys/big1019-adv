"""CI/CD 실습용 간단한 API: 장바구니 금액 계산."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Cart API")

FREE_SHIPPING_THRESHOLD = 50_000
SHIPPING_FEE = 3_000


class Item(BaseModel):
    price: int = Field(ge=0)
    qty: int = Field(ge=1, le=99)


def total_price(items: list[Item]) -> int:
    subtotal = sum(i.price * i.qty for i in items)
    return subtotal if subtotal >= FREE_SHIPPING_THRESHOLD or subtotal == 0 else subtotal + SHIPPING_FEE


@app.post("/cart/total")
def cart_total(items: list[Item]):
    return {"total": total_price(items)}


@app.get("/health")
def health():
    return {"status": "ok"}
