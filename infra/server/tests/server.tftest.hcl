mock_provider "aws" {}

variables {
  ssh_public_key = "ssh-rsa dGVzdA== test-only"
  ssh_cidr       = "192.0.2.1/32"
}

run "qa_isolated_access" {
  command = plan
  assert {
    condition     = aws_lightsail_instance.server.name == "takeaway-qa"
    error_message = "Default configuration must target QA."
  }
  assert {
    condition = alltrue([for rule in aws_lightsail_instance_public_ports.server.port_info :
      rule.from_port == 22 && rule.to_port == 22 && rule.cidrs == toset([var.ssh_cidr])
    ])
    error_message = "D7 must expose only SSH to the configured address."
  }
}

run "reject_public_ssh" {
  command = plan
  variables {
    ssh_cidr = "0.0.0.0/0"
  }
  expect_failures = [var.ssh_cidr]
}
