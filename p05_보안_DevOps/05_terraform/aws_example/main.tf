# ⚠ 읽기용 AWS 예시 — apply 하면 실제 자원이 생성되고 요금이 발생할 수 있습니다.
# S3(비공개 + 암호화 + 버전관리) / 보안 그룹(SSH는 내 IP만) / 최소 권한 IAM 정책

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # 팀 작업 시 상태 파일은 원격 저장 (S3 + 잠금)
  # backend "s3" {
  #   bucket       = "my-terraform-state"
  #   key          = "fridgechef/dev/terraform.tfstate"
  #   region       = "ap-northeast-2"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = "ap-northeast-2"
  default_tags {
    tags = { Project = "fridgechef", ManagedBy = "terraform" }
  }
}

variable "env" {
  type    = string
  default = "dev"
}

variable "my_ip_cidr" {
  description = "SSH를 허용할 내 공인 IP (예: 203.0.113.25/32)"
  type        = string
  validation {
    condition     = endswith(var.my_ip_cidr, "/32") && var.my_ip_cidr != "0.0.0.0/32"
    error_message = "SSH는 내 IP 한 개(/32)만 허용하세요."
  }
}

data "aws_vpc" "default" {
  default = true
}

# ---------------------------------------------------------------- S3
resource "aws_s3_bucket" "uploads" {
  bucket_prefix = "fridgechef-${var.env}-uploads-"
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration { status = "Enabled" }
}

# ---------------------------------------------------------------- 보안 그룹
resource "aws_security_group" "app" {
  name_prefix = "fridgechef-${var.env}-app-"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "SSH - my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------------------------------------------------------- IAM (앱 서버가 uploads 버킷만 읽고 쓰기)
data "aws_iam_policy_document" "app_s3" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.uploads.arn}/*"]
  }
}

resource "aws_iam_policy" "app_s3" {
  name_prefix = "fridgechef-${var.env}-app-s3-"
  policy      = data.aws_iam_policy_document.app_s3.json
}

output "bucket" {
  value = aws_s3_bucket.uploads.bucket
}

output "security_group_id" {
  value = aws_security_group.app.id
}
