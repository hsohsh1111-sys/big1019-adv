from fastapi.testclient import TestClient

from app.main import Item, app, total_price

client = TestClient(app)


def test_shipping_fee_added_below_threshold():
    assert total_price([Item(price=10_000, qty=2)]) == 23_000


def test_free_shipping_over_threshold():
    assert total_price([Item(price=25_000, qty=2)]) == 50_000


def test_empty_cart_is_zero():
    assert total_price([]) == 0


def test_api_validation():
    assert client.post("/cart/total", json=[{"price": 1000, "qty": 1}]).json() == {"total": 4000}
    assert client.post("/cart/total", json=[{"price": -1, "qty": 1}]).status_code == 422
