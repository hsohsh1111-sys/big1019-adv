"""리팩토링 전/후 비교 브라우저 실습 서버.

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import after
import before
import benchmark
from sample_data import make_orders

BASE = Path(__file__).parent
app = FastAPI(title="리팩토링 전/후 비교")


class BenchIn(BaseModel):
    sizes: list[int] = Field(default=[500, 1000, 2000], min_length=1, max_length=5)


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/api/code")
def code():
    return {name: (BASE / f"{name}.py").read_text(encoding="utf-8") for name in ("before", "after")}


@app.post("/api/benchmark")
def run_benchmark(body: BenchIn):
    sizes = [min(max(n, 1), 4000) for n in body.sizes]  # before는 O(n²)이라 너무 크면 오래 걸림 → 상한
    return benchmark.run_benchmark(sizes)


@app.get("/api/compare")
def compare(n: int = 1000):
    orders, vips = make_orders(min(max(n, 1), 4000))
    old, new = before.proc(orders, vips), after.build_report(orders, vips)
    return {"same": old == new, "before_total": old[1], "after_total": new[1],
            "duplicates": len(new[2]), "report_head": new[0].splitlines()[:5]}


@app.post("/api/test")
def run_tests():
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "test_refactoring.py"],
                          cwd=BASE, capture_output=True, text=True, timeout=120)
    return {"passed": proc.returncode == 0, "output": proc.stdout + proc.stderr}
