mock_provider "aws" {}
variables { environment = "qa" }
run "qa_logs_and_metrics" {
  command = plan
  assert {
    condition     = aws_cloudwatch_log_group.app.name == "/takeaway/qa/app" && aws_cloudwatch_log_group.app.retention_in_days == 3
    error_message = "QA logs must expire after three days in their own group."
  }
  assert {
    condition     = length(aws_cloudwatch_log_metric_filter.app) == 3 && alltrue([for metric in aws_cloudwatch_log_metric_filter.app : metric.log_group_name == aws_cloudwatch_log_group.app.name])
    error_message = "Exactly three metrics must use the environment app log group."
  }
}
run "prod_isolation" {
  command = plan
  variables { environment = "prod" }
  assert {
    condition     = aws_cloudwatch_log_group.app.name == "/takeaway/prod/app" && aws_cloudwatch_log_metric_filter.app["Requests"].metric_transformation[0].namespace == "Takeaway/prod"
    error_message = "Production logs and metrics must be separate from QA."
  }
}
