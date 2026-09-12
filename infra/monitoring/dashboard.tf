# One shared dashboard; only the QA monitoring state owns it.
resource "aws_cloudwatch_dashboard" "takeaway" {
  count          = var.environment == "qa" ? 1 : 0
  dashboard_name = "takeaway"
  dashboard_body = jsonencode({
    start          = "-PT3H"
    periodOverride = "inherit"
    widgets = concat([
      {
        type       = "text", x = 0, y = 0, width = 24, height = 2
        properties = { markdown = "# Takeaway - QA and production\nCounts use Sum per minute; latency uses Average in milliseconds. Health probes are excluded. Missing data means no samples, not confirmed zero errors. Managed by Terraform." }
      }
      ], [for index, chart in [
        { metric = "Requests", title = "Requests per minute", stat = "Sum", unit = "Count" },
        { metric = "ServerErrors", title = "Server errors (5xx) per minute", stat = "Sum", unit = "Count" },
        { metric = "Latency", title = "Average response time (ms)", stat = "Average", unit = "Milliseconds" }
        ] : {
        type = "metric", x = index * 8, y = 2, width = 8, height = 6
        properties = {
          title   = chart.title
          region  = "eu-north-1"
          view    = "timeSeries"
          stat    = chart.stat
          period  = 60
          stacked = false
          metrics = [
            ["Takeaway/qa", chart.metric, { label = "QA", color = "#ff7f0e" }],
            ["Takeaway/prod", chart.metric, { label = "Prod", color = "#1f77b4" }]
          ]
          yAxis = { left = { min = 0 } }
        }
    }])
  })
}
