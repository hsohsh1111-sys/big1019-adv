"""보안 그룹(방화벽) 위험 규칙 점검기.

입력: `aws ec2 describe-security-groups` 출력 형식의 JSON
실행:
  uvicorn web:app --reload                   # 브라우저 → http://127.0.0.1:8000 (아래쪽 보안 그룹 점검)
  python sg_audit.py                         # 샘플 security_groups.json 점검
  aws ec2 describe-security-groups > my.json && python sg_audit.py my.json   # 내 AWS 계정 점검 (조회만, 무료)
"""
import json
import sys
from pathlib import Path

SENSITIVE = {22: "SSH", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB"}
PUBLIC = {"0.0.0.0/0", "::/0"}


def audit(groups):
    findings = []
    for g in groups:
        for perm in g.get("IpPermissions", []):
            cidrs = [r["CidrIp"] for r in perm.get("IpRanges", [])] + [r["CidrIpv6"] for r in perm.get("Ipv6Ranges", [])]
            if not PUBLIC & set(cidrs):
                continue
            name = f"{g['GroupName']}({g['GroupId']})"
            if perm["IpProtocol"] == "-1":
                findings.append(("치명", name, "모든 프로토콜·포트", "인터넷 전체에 모든 포트 개방 → 즉시 삭제"))
                continue
            lo, hi = perm.get("FromPort", 0), perm.get("ToPort", 65535)
            exposed = [f"{p}/{svc}" for p, svc in SENSITIVE.items() if lo <= p <= hi]
            if exposed:
                level = "치명" if any(s in e for e in exposed for s in ("MySQL", "PostgreSQL", "Redis", "MongoDB")) else "높음"
                fix = "앱 서버 보안 그룹에서만 허용" if level == "치명" else "내 IP/32만 허용 또는 SSM Session Manager 사용"
                findings.append((level, name, ", ".join(exposed), fix))
            elif hi - lo > 100:
                findings.append(("보통", name, f"{lo}-{hi}", "필요한 포트만 개방"))
            elif lo not in (80, 443):
                findings.append(("낮음", name, f"{lo}", "공개가 꼭 필요한 포트인지 확인"))
    return findings


def audit_sorted(groups):
    return sorted(audit(groups), key=lambda f: ["치명", "높음", "보통", "낮음"].index(f[0]))


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "security_groups.json"
    groups = json.loads(path.read_text(encoding="utf-8"))["SecurityGroups"]
    findings = audit_sorted(groups)
    print(f"보안 그룹 {len(groups)}개 점검 — 발견 {len(findings)}건\n")
    for level, name, port, fix in findings:
        print(f"[{level}] {name:<22} 0.0.0.0/0 → {port:<14} 조치: {fix}")
    if not findings:
        print("위험한 공개 규칙이 없습니다 ✅")
    return 1 if any(f[0] == "치명" for f in findings) else 0  # CI에서 실패 처리할 수 있게 종료 코드 반환


if __name__ == "__main__":
    sys.exit(main())
