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

run "shared_dashboard" {
  command = plan
  assert {
    condition     = length(aws_cloudwatch_dashboard.takeaway) == 1 && aws_cloudwatch_dashboard.takeaway[0].dashboard_name == "takeaway"
    error_message = "QA must own exactly one shared dashboard."
  }
  assert {
    condition     = [for widget in slice(jsondecode(aws_cloudwatch_dashboard.takeaway[0].dashboard_body).widgets, 1, 4) : widget.properties.stat] == ["Sum", "Sum", "Average"]
    error_message = "Counts must use Sum and latency Average."
  }
  assert {
    condition     = alltrue([for widget in slice(jsondecode(aws_cloudwatch_dashboard.takeaway[0].dashboard_body).widgets, 1, 4) : widget.properties.period == 60 && widget.properties.metrics[0][0] == "Takeaway/qa" && widget.properties.metrics[1][0] == "Takeaway/prod"])
    error_message = "Every graph must compare both environments in one-minute periods."
  }
}
run "prod_does_not_own_dashboard" {
  command = plan
  variables { environment = "prod" }
  assert {
    condition     = length(aws_cloudwatch_dashboard.takeaway) == 0
    error_message = "Prod must not compete for the shared dashboard."
  }
}
