"""✅ 리팩토링 후: before.py 와 결과는 같고, 읽기 쉽고 빠른 코드."""
from collections import Counter

from sample_data import make_orders

VIP_DISCOUNT_RATE = 0.1
COUPON_DISCOUNTS = {"WELCOME": 5000}
FREE_SHIPPING_THRESHOLD = 50_000
SHIPPING_FEE = 3000


def subtotal(items):
    return sum(item["price"] * item["qty"] for item in items)


def final_price(order, vip_customers):
    price = subtotal(order["items"])
    if order["customer"] in vip_customers:
        price -= price * VIP_DISCOUNT_RATE
    price = max(price - COUPON_DISCOUNTS.get(order["coupon"], 0), 0)
    if price < FREE_SHIPPING_THRESHOLD:
        price += SHIPPING_FEE
    return price


def find_duplicate_ids(orders):
    counts = Counter(order["id"] for order in orders)  # O(n) 한 번 훑기
    return sorted(order_id for order_id, count in counts.items() if count > 1)


def build_report(orders, vip_customers):
    vip_set = set(vip_customers)  # 리스트 검색 O(n) → 집합 검색 O(1)
    prices = [final_price(order, vip_set) for order in orders]
    lines = [f"{o['id']},{o['customer']},{int(p)}\n" for o, p in zip(orders, prices, strict=True)]
    return "".join(lines), int(sum(prices)), find_duplicate_ids(orders)


if __name__ == "__main__":
    orders, vips = make_orders(3000)
    report, total, duplicates = build_report(orders, vips)
    print(f"총 매출 {total:,}원 / 중복 주문번호 {len(duplicates)}개")
