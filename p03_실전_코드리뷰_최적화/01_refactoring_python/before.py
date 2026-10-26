"""❌ 리팩토링 전: 동작은 하지만 읽기 어렵고 느린 코드 (리뷰 연습용)

리뷰 포인트를 직접 찾아보세요. (정답은 after.py 와 README.md)
"""
from sample_data import make_orders


def proc(d, v):
    r = ""
    t = 0
    dup = []
    for i in range(len(d)):
        o = d[i]
        s = 0
        for x in o["items"]:
            s = s + x["price"] * x["qty"]
        if o["customer"] in v:
            s = s - s * 0.1
        if o["coupon"] != None:
            if o["coupon"] == "WELCOME":
                s = s - 5000
                if s < 0:
                    s = 0
        if s >= 50000:
            s = s + 0
        else:
            s = s + 3000
        t = t + s
        r = r + o["id"] + "," + o["customer"] + "," + str(int(s)) + "\n"
        for j in range(len(d)):
            if i != j and d[i]["id"] == d[j]["id"]:
                if d[i]["id"] not in dup:
                    dup.append(d[i]["id"])
    return r, int(t), sorted(dup)


if __name__ == "__main__":
    orders, vips = make_orders(3000)
    report, total, duplicates = proc(orders, vips)
    print(f"총 매출 {total:,}원 / 중복 주문번호 {len(duplicates)}개")
