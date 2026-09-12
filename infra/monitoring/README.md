# D12 application logs and metrics

One three-day log group per environment: `/takeaway/qa/app` and
`/takeaway/prod/app`. Three metric filters publish Requests, ServerErrors (5xx),
and Latency (milliseconds), under `Takeaway/qa` and `Takeaway/prod`.
Health probes are excluded from metrics. View Latency using Average or percentiles;
use Sum for counts. Missing traffic produces missing metric data, not explicit zero.
Existing JSON request logging and payload redaction are unchanged.

Monitoring state is separate from servers: `monitoring/qa/terraform.tfstate` and
`monitoring/prod/terraform.tfstate`. QA PRs plan monitoring; merges apply each
environment before its app deployment, with the existing production approval.
Destroy monitoring before server infrastructure during teardown. Delete dashboard
and alarms first when later milestones add them. Metric history expires according
to AWS retention rather than being explicitly deleted.

## Approved permissions

Publishing-only `qa-permissions.json` and `prod-permissions.json` are already
attached as inline TakeawayAppLogs policies. The additional
`qa-management-permissions.json` and `prod-management-permissions.json` were explicitly approved and attached as inline TakeawayMonitoring policies:

- Manage only the matching environment app log group, retention, tags and metric
  filters. DeleteLogGroup and DeleteMetricFilter are included for Terraform teardown.
- Describe log groups in eu-north-1 (AWS requires wildcard resource for discovery).
- Read/write only that environment's monitoring state and manage its lock file in
  the existing state bucket; list the bucket for backend initialization.
- No dashboard, alarm, IAM management or direct PutMetricData permissions.

Both attached management policies were read back from AWS and matched these files.
No keys should appear in files, Terraform state, logs, Git, or PR descriptions.

## Runtime

The user explicitly chose to reuse each environment's deployment credentials.
Actions passes them through encrypted SSH stdin into the Docker host's root-only
`/root/.aws/credentials` file. A small one-off Alpine container writes that file
because the deploy user already has Docker access. The app container never receives
AWS credentials. These reused credentials retain their existing infrastructure
permissions; the user accepted that tradeoff. Existing unrelated root AWS profiles
are not supported on these dedicated challenge servers.

The `.cloudwatch-enabled` marker selects the Compose logging override on subsequent
manual redeployments too. Only app stdout/stderr is forwarded. `docker logs` retains
bounded local cached logs (two 10 MB files). Non-blocking delivery uses a 1 MB buffer;
if CloudWatch is unreachable and it fills, messages can be dropped. Logging-driver
initialization can still fail deployment if credentials or the log group are missing.
Recreating the server removes local credentials and markers; Actions reinstalls them.
Credential rotation may require restarting Docker to clear cached driver credentials.

## Verification after merge

1. Confirm QA deploy passes, then approve prod.
2. Make an application request; note its X-Request-ID header.
3. Find that request ID in the matching CloudWatch app log group.
4. Confirm the other environment's logs are in its separate group.
5. Check Requests and Latency metrics after delivery. A controlled 5xx test and
   notification testing belong to the alarm milestone; don't force production errors.

Nine local deployment tests, two Terraform mock tests, Compose config, actionlint
and shell validation cover the code. Live publishing and metric delivery remain
pending approved permissions and the Actions run. No resource apply was run locally.


## D13 shared dashboard

The `takeaway` dashboard compares QA/prod Requests (Sum), ServerErrors (Sum),
and Latency (Average), at one-minute periods over the last three hours. Missing
samples remain gaps rather than being presented as confirmed zero errors.
The QA monitoring state owns this single shared resource; prod creates no dashboard.
It uses existing metrics and creates no additional metrics or log ingestion.

`qa-dashboard-permissions.json` was approved and attached: GetDashboard, PutDashboard
and DeleteDashboards only for `arn:aws:cloudwatch::455958489157:dashboard/takeaway`.
Delete is needed for the agreed complete teardown. Prod needs no new permissions.
Attached to github-actions-qa as inline TakeawayDashboard; AWS readback verified.
After merge, open CloudWatch > Dashboards > takeaway and verify both series and
correct statistics. This changes dashboard presentation only, not production data.
