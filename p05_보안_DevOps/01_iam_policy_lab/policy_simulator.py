"""IAM 정책 평가 시뮬레이터 (학습용, AWS 계정 불필요).

AWS 정책 평가 규칙을 단순화해 구현했다.
  1) 기본은 거부(묵시적 Deny)  2) Allow가 있으면 허용  3) 명시적 Deny가 하나라도 있으면 무조건 거부
지원: Action/Resource 와일드카드(*), Condition의 Bool·IpAddress·StringEquals

실행: python policy_simulator.py            # 시나리오 일괄 판정 + 과도한 권한 점검
"""
import ipaddress
import json
from fnmatch import fnmatchcase
from pathlib import Path

POLICY_DIR = Path(__file__).parent / "policies"


def as_list(v):
    return v if isinstance(v, list) else [v]


def condition_ok(cond, ctx):
    for operator, pairs in (cond or {}).items():
        for key, expected in pairs.items():
            actual = ctx.get(key)
            if operator == "Bool" and str(actual).lower() != str(expected).lower():
                return False
            if operator == "StringEquals" and actual not in as_list(expected):
                return False
            if operator == "IpAddress" and (actual is None or not any(
                    ipaddress.ip_address(actual) in ipaddress.ip_network(c) for c in as_list(expected))):
                return False
    return True


def matches(stmt, action, resource, ctx):
    return (any(fnmatchcase(action.lower(), a.lower()) for a in as_list(stmt["Action"]))
            and any(fnmatchcase(resource, r) for r in as_list(stmt["Resource"]))
            and condition_ok(stmt.get("Condition"), ctx))


def evaluate(policies, action, resource, ctx=None):
    ctx = ctx or {}
    hits = [(name, s) for name, p in policies.items() for s in p["Statement"] if matches(s, action, resource, ctx)]
    denies = [f"{n}:{s.get('Sid', '?')}" for n, s in hits if s["Effect"] == "Deny"]
    allows = [f"{n}:{s.get('Sid', '?')}" for n, s in hits if s["Effect"] == "Allow"]
    if denies:
        return "DENY", f"명시적 거부 {denies}"
    if allows:
        return "ALLOW", f"허용 {allows}"
    return "DENY", "일치하는 Allow 없음 (묵시적 거부)"


def lint(name, policy):
    """최소 권한 원칙 위반 점검."""
    warnings = []
    for s in policy["Statement"]:
        if s["Effect"] != "Allow":
            continue
        acts, res = as_list(s["Action"]), as_list(s["Resource"])
        if "*" in acts:
            warnings.append(f"[치명] {name}:{s.get('Sid')} — 모든 Action 허용 (\"*\")")
        elif any(a.endswith(":*") for a in acts) and "*" in res:
            warnings.append(f"[높음] {name}:{s.get('Sid')} — 서비스 전체 권한을 모든 리소스에 허용")
        elif "*" in res and not s.get("Condition"):
            warnings.append(f"[보통] {name}:{s.get('Sid')} — Resource \"*\" (조건 없음)")
    return warnings


SCENARIOS = [
    # (설명, 적용 정책, action, resource, 요청 컨텍스트)
    ("업로드 파일 읽기", ["s3_readonly_uploads"], "s3:GetObject", "arn:aws:s3:::myapp-uploads/a.png", {}),
    ("업로드 파일 삭제", ["s3_readonly_uploads"], "s3:DeleteObject", "arn:aws:s3:::myapp-uploads/a.png", {}),
    ("다른 버킷 읽기", ["s3_readonly_uploads"], "s3:GetObject", "arn:aws:s3:::payroll/salary.xlsx", {}),
    ("개발 버킷 파일 삭제", ["developer"], "s3:DeleteObject", "arn:aws:s3:::myapp-dev-logs/x.log", {}),
    ("운영 버킷 파일 삭제", ["developer", "too_permissive"], "s3:DeleteObject", "arn:aws:s3:::myapp-prod-db/backup.sql", {}),
    ("사무실에서 EC2 중지", ["developer"], "ec2:StopInstances", "arn:aws:ec2:ap-northeast-2:1:instance/i-1",
     {"aws:SourceIp": "203.0.113.25"}),
    ("카페에서 EC2 중지", ["developer"], "ec2:StopInstances", "arn:aws:ec2:ap-northeast-2:1:instance/i-1",
     {"aws:SourceIp": "198.51.100.7"}),
    ("MFA 없이 IAM 사용자 생성", ["developer", "too_permissive"], "iam:CreateUser", "arn:aws:iam::1:user/new",
     {"aws:MultiFactorAuthPresent": "false"}),
    ("MFA 후 IAM 사용자 생성", ["developer", "too_permissive"], "iam:CreateUser", "arn:aws:iam::1:user/new",
     {"aws:MultiFactorAuthPresent": "true"}),
]


def main():
    policies = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in POLICY_DIR.glob("*.json")}
    print("■ 시나리오 판정\n")
    for desc, names, action, resource, ctx in SCENARIOS:
        decision, reason = evaluate({n: policies[n] for n in names}, action, resource, ctx)
        mark = "✅" if decision == "ALLOW" else "❌"
        print(f"{mark} {decision:<5} {desc:<22} [{', '.join(names)}]\n         {action} → {reason}")
    print("\n■ 최소 권한 점검")
    for name, policy in policies.items():
        for w in lint(name, policy) or [f"[양호] {name}"]:
            print("  " + w)


if __name__ == "__main__":
    main()
