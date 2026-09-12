terraform {
  required_version = ">= 1.10, < 2.0"
  backend "s3" {}
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region              = "eu-north-1"
  allowed_account_ids = ["455958489157"]
}

variable "environment" {
  type    = string
  default = "qa"
  validation {
    condition     = contains(["qa", "prod"], var.environment)
    error_message = "Use qa or prod with its separate backend state."
  }
}

variable "ssh_public_key" {
  type = string
  validation {
    condition     = startswith(trimspace(var.ssh_public_key), "ssh-rsa ")
    error_message = "Provide an RSA OpenSSH public key, never a private key."
  }
}

locals {
  name = "takeaway-${var.environment}"
  tags = {
    Project     = "takeaway"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_lightsail_key_pair" "server" {
  name       = local.name
  public_key = trimspace(var.ssh_public_key)
  tags       = local.tags
}

resource "aws_lightsail_instance" "server" {
  name              = local.name
  availability_zone = "eu-north-1a"
  blueprint_id      = "ubuntu_24_04"
  bundle_id         = "small_3_0"
  ip_address_type   = "ipv4"
  key_pair_name     = aws_lightsail_key_pair.server.name
  tags              = local.tags

  user_data = "#cloud-config\n${yamlencode({
    package_update = true
    packages       = ["docker.io", "docker-compose-v2"]
    ssh_pwauth     = false
    users = ["default", {
      name                = "deploy"
      groups              = "docker"
      shell               = "/bin/bash"
      lock_passwd         = true
      ssh_authorized_keys = [trimspace(var.ssh_public_key)]
    }]
    runcmd = [
      ["systemctl", "enable", "--now", "docker"],
      ["install", "-d", "-o", "deploy", "-g", "deploy", "/opt/takeaway"]
    ]
  })}"
}

# D7 exposes SSH only. Web ports are added when the application needs them.
resource "aws_lightsail_instance_public_ports" "server" {
  instance_name = aws_lightsail_instance.server.name
  port_info {
    protocol  = "tcp"
    from_port = 22
    to_port   = 22
    cidrs     = ["0.0.0.0/0"]
  }
}

output "public_ip" {
  value = aws_lightsail_instance.server.public_ip_address
}

output "ssh_user" {
  value = "deploy"
}
