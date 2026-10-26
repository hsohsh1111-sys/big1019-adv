"""테스트·벤치마크용 주문 데이터 생성."""
import random


def make_orders(n, seed=42):
    rng = random.Random(seed)
    products = [("키보드", 39000), ("마우스", 19000), ("모니터", 189000), ("USB 허브", 12000), ("웹캠", 45000)]
    orders = []
    for _ in range(n):
        picked = rng.sample(products, rng.randint(1, 3))
        items = [{"name": name, "price": price, "qty": rng.randint(1, 3)} for name, price in picked]
        order_id = f"O{rng.randint(1, n):06d}"  # 일부러 중복 주문번호가 생기게 함
        orders.append({"id": order_id, "customer": f"user{rng.randint(1, n // 2 + 1)}", "items": items,
                       "coupon": rng.choice([None, None, "WELCOME"])})
    vip_customers = [f"user{i}" for i in range(1, n // 2 + 1, 7)]
    return orders, vip_customers
