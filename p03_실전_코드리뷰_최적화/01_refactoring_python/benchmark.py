"""before vs after 속도 비교.  실행: python benchmark.py"""
import timeit

import after
import before
from sample_data import make_orders

for n in (500, 1000, 2000, 4000):
    orders, vips = make_orders(n)
    t_before = timeit.timeit(lambda o=orders, v=vips: before.proc(o, v), number=1)
    t_after = timeit.timeit(lambda o=orders, v=vips: after.build_report(o, v), number=1)
    print(f"주문 {n:>5}건 | before {t_before * 1000:9.1f} ms | after {t_after * 1000:7.1f} ms | {t_before / t_after:6.0f}배 빠름")

print("\n주문 수가 2배가 될 때 before 는 약 4배(O(n²)), after 는 약 2배(O(n))로 늘어나는 것을 확인하세요.")
