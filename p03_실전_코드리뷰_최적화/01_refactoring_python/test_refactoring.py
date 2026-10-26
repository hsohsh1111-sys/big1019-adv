"""리팩토링 안전망: before 와 after 가 같은 결과를 내는지 확인한다.  실행: pytest -q"""
import pytest

import after
import before
from sample_data import make_orders


@pytest.mark.parametrize("n", [0, 1, 10, 500])
def test_same_result_as_before(n):
    orders, vips = make_orders(n) if n else ([], [])
    assert after.build_report(orders, vips) == before.proc(orders, vips)


def test_final_price_rules():
    item = lambda price, qty=1: {"price": price, "qty": qty}  # noqa: E731
    order = lambda items, customer="kim", coupon=None: {"items": items, "customer": customer, "coupon": coupon}  # noqa: E731
    assert after.final_price(order([item(10000)]), set()) == 13000                  # 배송비 추가
    assert after.final_price(order([item(60000)]), set()) == 60000                  # 무료 배송
    assert after.final_price(order([item(60000)]), {"kim"}) == 54000                # VIP 10%
    assert after.final_price(order([item(2000)], coupon="WELCOME"), set()) == 3000  # 쿠폰이 금액보다 커도 0원 미만 X


def test_find_duplicate_ids():
    orders = [{"id": "A"}, {"id": "B"}, {"id": "A"}, {"id": "C"}, {"id": "B"}]
    assert after.find_duplicate_ids(orders) == ["A", "B"]
