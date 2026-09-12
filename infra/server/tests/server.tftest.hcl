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
    condition     = aws_lightsail_instance.server.name == "takeaway-prod" && aws_lightsail_key_pair.server.name == "takeaway-prod-ssh"
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
    condition     = aws_lightsail_key_pair.server.name == "takeaway-qa-ssh" && aws_lightsail_instance.server.key_pair_name == aws_lightsail_key_pair.server.name
    error_message = "The SSH key must have a distinct name and be referenced by the instance."
  }
  assert {
    condition = length(aws_lightsail_instance_public_ports.server.port_info) == 1 && alltrue([for rule in aws_lightsail_instance_public_ports.server.port_info :
      rule.protocol == "tcp" && rule.from_port == 22 && rule.to_port == 22 && rule.cidrs == toset(["0.0.0.0/0"])
    ])
    error_message = "D7 must expose only TCP SSH, from any IPv4 address."
  }
  assert {
    condition     = strcontains(aws_lightsail_instance.server.user_data, "PasswordAuthentication no")
    error_message = "Public SSH must keep password login disabled."
  }
  assert {
    condition     = startswith(aws_lightsail_instance.server.user_data, "#!/bin/bash\n") && strcontains(aws_lightsail_instance.server.user_data, base64encode(var.ssh_public_key))
    error_message = "Lightsail must receive a shell script containing the supplied public key."
  }
}
