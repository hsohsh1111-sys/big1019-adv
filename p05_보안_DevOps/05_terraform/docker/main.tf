# Docker Provider로 nginx 컨테이너를 코드로 생성 (Docker Desktop 필요, 비용 0원)
#   terraform init && terraform apply   →  http://localhost:8081
#   terraform destroy

terraform {
  required_version = ">= 1.5"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Windows Docker Desktop: host = "npipe:////./pipe/docker_engine"
# macOS / Linux:          host = "unix:///var/run/docker.sock"
provider "docker" {}

variable "external_port" {
  type    = number
  default = 8081
}

resource "docker_image" "nginx" {
  name         = "nginx:1.27-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "tf-nginx"
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = var.external_port
  }

  upload {
    file    = "/usr/share/nginx/html/index.html"
    content = "<h1>Terraform으로 만든 컨테이너</h1><p>port ${var.external_port}</p>"
  }
}

output "url" {
  value = "http://localhost:${var.external_port}"
}
