"""IAM 정책 시뮬레이터 & 보안 그룹 점검 브라우저 실습 서버 (AWS 계정 불필요).

실행: uvicorn web:app --reload  →  http://127.0.0.1:8000
"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import policy_simulator as sim
import sg_audit

BASE = Path(__file__).parent
app = FastAPI(title="IAM 정책 & 보안 그룹 실습")


class EvaluateIn(BaseModel):
    policies: list[str] = Field(default=[])
    custom: dict | None = None  # 화면에서 직접 작성한 정책 (선택)
    action: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    context: dict[str, str] = {}


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/api/policies")
def policies():
    return sim.load_policies()


@app.get("/api/scenarios")
def scenarios():
    return [{"desc": d, "policies": p, "action": a, "resource": r, "context": c} for d, p, a, r, c in sim.SCENARIOS]


@app.post("/api/evaluate")
def evaluate(body: EvaluateIn):
    all_policies = sim.load_policies()
    selected = {n: all_policies[n] for n in body.policies if n in all_policies}
    if body.custom:
        selected["custom"] = body.custom
    context = {k: v for k, v in body.context.items() if v}  # 빈 값은 "요청에 없는 정보"로 취급
    try:
        decision, reason = sim.evaluate(selected, body.action, body.resource, context)
    except (KeyError, TypeError, ValueError) as e:  # 정책 형식 오류, 잘못된 IP 등
        raise HTTPException(400, f"정책 또는 입력 형식 오류: {e}") from e
    return {"decision": decision, "reason": reason}


@app.get("/api/lint")
def lint():
    return [w for name, p in sim.load_policies().items() for w in sim.lint(name, p) or [f"[양호] {name}"]]


@app.get("/api/sg-audit")
def sg():
    groups = json.loads((BASE / "security_groups.json").read_text(encoding="utf-8"))["SecurityGroups"]
    findings = sg_audit.audit_sorted(groups)
    return {"groups": len(groups),
            "findings": [{"level": lv, "group": g, "port": p, "fix": f} for lv, g, p, f in findings]}
