# 05. Terraform — 비용 0원으로 IaC 체험

[Terraform 설치](https://developer.hashicorp.com/terraform/install) (Windows: `winget install Hashicorp.Terraform`)

## A. local/ — 클라우드 없이 Terraform 흐름 익히기

```bash
cd local
terraform init            # Provider 다운로드 (.terraform/ 폴더)
terraform fmt -check      # 코드 형식 검사
terraform validate        # 문법 검사
terraform plan            # + create 3개 미리보기
terraform apply           # yes 입력 → out/dev/config.json, out/prod/config.json, out/README.txt 생성
terraform output
```

### 변경 체험

`main.tf`의 `prod`를 `instance_count = 3`으로 바꾼 뒤

```bash
terraform plan            # -/+ local_file.env_config["prod"] must be replaced  → 1개만 교체
terraform apply
```

- `staging` 환경을 `environments`에 추가 → plan에서 `+ create` 1개
- `instance_count = 10` → `validation` 규칙에 걸려 plan 단계에서 차단
- `out/dev/config.json`을 손으로 수정한 뒤 `terraform plan` → **드리프트 감지**(다시 생성하려 함)

```bash
terraform destroy         # 모두 삭제
```

## B. docker/ — 실제 "인프라"(컨테이너)를 코드로 (Docker Desktop 필요)

```bash
cd docker
terraform init && terraform apply     # http://localhost:8081
docker ps                             # tf-nginx 컨테이너 확인
terraform apply -var external_port=8082   # 포트 변경 → 컨테이너 교체
terraform destroy
```

## C. aws_example/ — 읽기용 AWS 코드

S3(퍼블릭 차단·암호화·버전 관리), 보안 그룹(SSH는 내 IP만, `validation`으로 강제), 최소 권한 IAM 정책 예시입니다.
**apply 시 요금이 발생할 수 있으므로** 실행은 선택이며, 실행한다면 반드시 `terraform destroy`로 정리하세요.

```bash
cd aws_example
terraform init
terraform plan -var my_ip_cidr="$(curl -s https://checkip.amazonaws.com)/32"   # plan은 자원을 만들지 않음 (AWS 자격 증명 필요)
```

## Git에 올리면 안 되는 파일

`.terraform/`, `*.tfstate`, `*.tfstate.backup`, `*.tfvars`(비밀 값 포함 시) — 저장소 루트 `.gitignore`에 등록되어 있습니다.
`.terraform.lock.hcl`은 Provider 버전 고정용이므로 **커밋하는 것이 권장**됩니다.
