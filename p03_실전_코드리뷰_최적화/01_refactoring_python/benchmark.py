"""before vs after 속도 비교.  실행: python benchmark.py  (브라우저: uvicorn web:app --reload)"""
import timeit

import after
import before
from sample_data import make_orders


def run_benchmark(sizes=(500, 1000, 2000, 4000)):
    rows = []
    for n in sizes:
        orders, vips = make_orders(n)
        t_before = timeit.timeit(lambda o=orders, v=vips: before.proc(o, v), number=1)
        t_after = timeit.timeit(lambda o=orders, v=vips: after.build_report(o, v), number=1)
        rows.append({"n": n, "before_ms": round(t_before * 1000, 1), "after_ms": round(t_after * 1000, 1),
                     "speedup": round(t_before / t_after)})
    return rows


if __name__ == "__main__":
    for r in run_benchmark():
        print(f"주문 {r['n']:>5}건 | before {r['before_ms']:9.1f} ms | after {r['after_ms']:7.1f} ms | "
              f"{r['speedup']:6}배 빠름")
    print("\n주문 수가 2배가 될 때 before 는 약 4배(O(n²)), after 는 약 2배(O(n))로 늘어나는 것을 확인하세요.")
