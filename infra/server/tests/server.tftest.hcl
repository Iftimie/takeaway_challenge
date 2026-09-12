mock_provider "aws" {}

variables {
  environment    = "qa"
  ssh_public_key = "ssh-rsa dGVzdA== test-only"
}

run "prod_has_separate_resource_names" {
  command = plan
  variables {
    environment = "prod"
  }
  assert {
    condition     = aws_lightsail_instance.server.name == "takeaway-prod" && aws_lightsail_key_pair.server.name == "takeaway-prod"
    error_message = "Production must not reuse QA resource names."
  }
  assert {
    condition     = aws_lightsail_instance.server.tags.Environment == "prod"
    error_message = "Production must carry its own environment tag for IAM isolation."
  }
}

run "qa_key_based_ssh" {
  command = plan
  assert {
    condition     = aws_lightsail_instance.server.name == "takeaway-qa"
    error_message = "Default configuration must target QA."
  }
  assert {
    condition = length(aws_lightsail_instance_public_ports.server.port_info) == 1 && alltrue([for rule in aws_lightsail_instance_public_ports.server.port_info :
      rule.protocol == "tcp" && rule.from_port == 22 && rule.to_port == 22 && rule.cidrs == toset(["0.0.0.0/0"])
    ])
    error_message = "D7 must expose only TCP SSH, from any IPv4 address."
  }
  assert {
    condition     = yamldecode(aws_lightsail_instance.server.user_data).ssh_pwauth == false
    error_message = "Public SSH must keep password login disabled."
  }
  assert {
    condition     = yamldecode(aws_lightsail_instance.server.user_data).users[1].ssh_authorized_keys == [var.ssh_public_key]
    error_message = "The deployment account must use the supplied SSH public key."
  }
}
