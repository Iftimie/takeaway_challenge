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
  type = string
  validation {
    condition     = contains(["qa", "prod"], var.environment)
    error_message = "Use qa or prod."
  }
}
resource "aws_cloudwatch_log_group" "app" {
  name              = "/takeaway/${var.environment}/app"
  retention_in_days = 3
  tags              = { Project = "takeaway", Environment = var.environment }
}
locals {
  metrics = {
    Requests     = { pattern = "{ $.request_id = * && $.status = * && $.route != \"/health\" }", value = "1", unit = "Count" }
    ServerErrors = { pattern = "{ $.request_id = * && $.status >= 500 && $.route != \"/health\" }", value = "1", unit = "Count" }
    Latency      = { pattern = "{ $.request_id = * && $.duration_ms >= 0 && $.route != \"/health\" }", value = "$.duration_ms", unit = "Milliseconds" }
  }
}
resource "aws_cloudwatch_log_metric_filter" "app" {
  for_each       = local.metrics
  name           = each.key
  log_group_name = aws_cloudwatch_log_group.app.name
  pattern        = each.value.pattern
  metric_transformation {
    name      = each.key
    namespace = "Takeaway/${var.environment}"
    value     = each.value.value
    unit      = each.value.unit
  }
}
