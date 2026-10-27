# p05. 보안 및 DevOps

> 클라우드 접근 제어(IAM·보안 그룹)를 시뮬레이터로 실험하고, Docker·Kubernetes로 컨테이너를 배포하고, CI/CD로 배포를 자동화하고, Terraform으로 인프라를 코드로 관리합니다. 모든 예제는 결과를 **브라우저에서 확인**할 수 있고, AWS 비용 없이 실습할 수 있습니다.

각 예제 폴더의 `README.md`는 **1. 개념 → 2. 예제 → 3. 코드 분석 → 4. 테스트 방법** 순서로 구성되어 있습니다.

## 예제 목록

| 폴더 | 학습 주제 | 브라우저 예제 | 실행 |
|---|---|---|---|
| [01_iam_policy_lab](01_iam_policy_lab) | 클라우드 보안 정책·접근 제어 (IAM, VPC, 네트워크 보안) | IAM 정책 시뮬레이터 + 보안 그룹 점검 | `uvicorn web:app --reload` → :8000 |
| [02_docker](02_docker) | Docker 컨테이너 환경 구성 | 방문자 카운터 (memory → Redis) | `uvicorn app.main:app --reload` / `docker compose up` → :8000 |
| [03_kubernetes](03_kubernetes) | Kubernetes 배포 | 같은 앱을 Pod 3개로 → 로드밸런싱·자가 치유·롤링 업데이트 | `kubectl apply -f k8s/` → :30080 |
| [04_cicd](04_cicd) | CI/CD (GitHub Actions, Jenkins) | 장바구니 API + 배포 버전(커밋 SHA) 배지 | `uvicorn app.main:app --reload` → :8000 |
| [05_terraform](05_terraform) | IaC 인프라 자동화 | `terraform apply` → HTML 대시보드 / nginx 컨테이너 | `terraform apply` → `out/index.html`, :8081 |

## 공통 준비

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS/Linux: source .venv/bin/activate)
pip install fastapi "uvicorn[standard]" redis pytest httpx ruff
```

| 도구 | 필요한 예제 | 설치 (Windows) |
|---|---|---|
| Docker Desktop | 02, 03, 04(빌드), 05(docker) | https://www.docker.com/products/docker-desktop |
| kind, kubectl | 03 | `winget install Kubernetes.kind Kubernetes.kubectl` |
| Terraform | 05 | `winget install Hashicorp.Terraform` |

> 01, 02(Docker 없이), 04(로컬 CI 단계)는 파이썬만으로 실행할 수 있습니다.
