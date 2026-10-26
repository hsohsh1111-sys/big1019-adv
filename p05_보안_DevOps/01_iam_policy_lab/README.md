# 01. IAM 정책 & 보안 그룹 실습 (AWS 계정 불필요)

```bash
python policy_simulator.py   # 추가 설치 없음 (표준 라이브러리만 사용)
python sg_audit.py
```

## A. IAM 정책 시뮬레이터

`policies/` 폴더의 정책을 조합해 요청이 허용되는지 판정합니다.

| 정책 파일 | 내용 |
|---|---|
| `s3_readonly_uploads.json` | 특정 버킷 읽기만 허용 (최소 권한의 좋은 예) |
| `developer.json` | 개발 버킷 관리 + **사무실 IP에서만** EC2 시작/중지 + 운영 데이터 삭제 **Deny** + **MFA 없으면** IAM Deny |
| `too_permissive.json` | `"Action": "*"` (나쁜 예) |

```
❌ DENY  운영 버킷 파일 삭제   [developer, too_permissive]
         s3:DeleteObject → 명시적 거부 ['developer:NeverDeleteProdData']
❌ DENY  카페에서 EC2 중지    [developer]
         ec2:StopInstances → 일치하는 Allow 없음 (묵시적 거부)
```

**관찰 포인트**: `too_permissive`가 모든 것을 허용해도, `developer`의 **명시적 Deny가 이깁니다.** 실무에서는 이 원리로 조직 전체에 "절대 금지" 규칙(SCP, 권한 경계)을 겁니다.

**도전**: `developer.json`에 "`ap-northeast-2` 리전 외에는 EC2 사용 금지" Deny 문을 추가해 보세요. (`StringEquals` + `aws:RequestedRegion`, 시나리오에 컨텍스트 추가)

## B. 보안 그룹 점검기

```
[치명] database(sg-0db)       0.0.0.0/0 → 3306/MySQL     조치: 앱 서버 보안 그룹에서만 허용
[치명] temp-debug(sg-0tmp)    0.0.0.0/0 → 모든 프로토콜·포트   조치: 즉시 삭제
[높음] app-server(sg-0app)    0.0.0.0/0 → 22/SSH         조치: 내 IP/32만 허용 또는 SSM Session Manager 사용
```

- 치명 항목이 있으면 **종료 코드 1**을 반환 → CI 파이프라인에서 배포를 막는 데 쓸 수 있습니다.
- 본인 AWS 계정이 있다면 `aws ec2 describe-security-groups > my.json` (조회만, 무료) 후 `python sg_audit.py my.json`으로 실제 점검이 가능합니다.
