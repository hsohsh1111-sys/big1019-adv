# 클라우드 비용 0원 Terraform 실습: local Provider로 "환경별 설정 파일"이라는 인프라를 코드로 관리
#   terraform init → terraform plan → terraform apply → (변수 수정) → plan → apply → terraform destroy

terraform {
  required_version = ">= 1.5"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

variable "project" {
  description = "프로젝트 이름"
  type        = string
  default     = "fridgechef"
}

variable "environments" {
  description = "환경별 설정 (이 값을 바꾸고 plan을 실행해 보세요)"
  type = map(object({
    instance_count = number
    instance_type  = string
    debug          = bool
  }))
  default = {
    dev  = { instance_count = 1, instance_type = "t3.micro", debug = true }
    prod = { instance_count = 2, instance_type = "t3.small", debug = false }
  }

  validation {
    condition     = alltrue([for e in values(var.environments) : e.instance_count >= 1 && e.instance_count <= 5])
    error_message = "instance_count 는 1~5 사이여야 합니다."
  }
}

locals {
  common_tags = { Project = var.project, ManagedBy = "terraform" }
}

# for_each: 환경 수만큼 자원을 반복 생성
resource "local_file" "env_config" {
  for_each = var.environments

  filename = "${path.module}/out/${each.key}/config.json"
  content = jsonencode(merge(local.common_tags, {
    Env           = each.key
    InstanceCount = each.value.instance_count
    InstanceType  = each.value.instance_type
    Debug         = each.value.debug
    ApiUrl        = "https://${each.key == "prod" ? "" : "${each.key}."}api.${var.project}.example.com"
  }))
}

resource "local_file" "readme" {
  filename = "${path.module}/out/README.txt"
  content  = "이 폴더는 Terraform이 관리합니다. 직접 수정하지 마세요.\n환경: ${join(", ", keys(var.environments))}\n"
}

output "config_files" {
  value = { for env, f in local_file.env_config : env => f.filename }
}

output "total_instances" {
  value = sum([for e in values(var.environments) : e.instance_count])
}
