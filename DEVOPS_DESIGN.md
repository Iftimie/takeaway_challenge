# Deployment design

Status: D1 accepted; delivery design amended by user agreement to GHCR and SSH.
The D4 state bucket now exists; consult the progress tracker for resource status.
Milestone status and next actions live in [DEVOPS_PROGRESS.md](DEVOPS_PROGRESS.md).

## Purpose and boundaries

Run QA and prod for short development/demo sessions, usually 1–2 days, then
destroy everything created for this deployment. Both databases are disposable.
This extends the challenge with deployment practice; it is not a highly available
production architecture. Each environment depends on a single server.

Use two AWS Lightsail Linux instances, initially proposing 2 GB RAM each.
Each runs Docker Compose with Nginx, the existing FastAPI/Uvicorn application
(including the built Vue UI), and PostgreSQL with a local persistent volume.
QA and prod have separate servers, databases, passwords, JWT secrets and SSH keys.
Redeploying the application preserves its database; teardown deletes it.

AWS region: `eu-north-1` (user selected).
Repository: https://github.com/Iftimie/takeaway_challenge (user supplied; intended public).
No Git remote was configured when D1 was inspected; recording this URL does not configure it.

## Request and release flow

Browser -> environment public IP over HTTP -> Nginx -> app -> PostgreSQL.
SSH is reachable from any IPv4 address, with key authentication and password login
disabled (user-selected simplification). Web ports are added with deployment. Neither Uvicorn
nor PostgreSQL needs a public port. The UI and API share an origin.
HTTPS was canceled by the user in D9; use public HTTP for this challenge.
No domain, load balancer, managed database or Kubernetes is planned.

GitHub Actions runs Python, JavaScript and browser tests using a disposable test
database. A successful run builds and publishes a public image to GitHub Container
Registry (GHCR). QA deploys it
and runs smoke checks. A GitHub production environment approval then permits
deploying the same image digest to prod. A digest identifies the exact image
contents, so approval cannot accidentally promote a different build.

GitHub publishes with its built-in token and uses separate environment SSH keys
to deploy to the servers. Servers pull public images without registry credentials.
There is no AWS OIDC integration. Terraform runs in GitHub Actions using dedicated
IAM user access keys stored separately in each GitHub environment. QA uses
github-actions-qa with custom Lightsail and QA-state permissions. Bootstrap and
teardown run locally using browser-login credentials. Infrastructure changes use reviewed plans;
ordinary application deployment does not recreate infrastructure. Serialize
deployments per environment. Run migrations before starting the updated app.
Sample-data reset remains an explicit destructive action, never a deployment step.

User-selected trigger strategy: opened/updated PRs targeting main run tests and QA
planning; merged PRs run tests then QA apply, production approval and combined
prod plan/apply. Only qa and prod environments and their existing IAM users are
used. Infrastructure steps run only for infra/server or .github changes. QA PR
planning uses write-capable credentials. Fork PRs run tests and credential-free
Terraform validation only. Production approval precedes the fresh plan, which is
immediately applied on the same runner. See infra/server/PIPELINE.md.
This infrastructure flow is being introduced ahead of app deployment/smoke checks;
those remain pending, so successful provisioning does not establish app health.

## Resource ownership and proposed names

Terraform owns AWS resources; Compose owns containers and database volumes;
GitHub settings own approvals and secret storage. Never put secret values in Git.
Use `Project=takeaway`, `Environment=qa|prod|shared` and `ManagedBy=terraform`
tags where supported. Names below are proposals, not existing resources.

| Group | Resources | Naming / state boundary |
|---|---|---|
| Bootstrap | Private encrypted, versioned S3 state bucket with state locking | `takeaway-tfstate-<account-id>-<region>`; separate bootstrap state |
| Shared delivery | Public GHCR package, GitHub QA/prod environments and dedicated infrastructure IAM users | Package `ghcr.io/iftimie/takeaway_challenge`; IAM users/keys configured manually and included in final cleanup |
| QA | Lightsail instance, firewall rules, SSH public key and any explicitly allocated IP | `takeaway-qa`; `qa/terraform.tfstate` |
| Prod | Equivalent independent resources | `takeaway-prod`; `prod/terraform.tfstate` |
| Monitoring | Log groups, metric definitions/filters as needed, one dashboard, per-environment alarms, SNS email notifications | Logs `/takeaway/qa/app`, `/takeaway/prod/app`; dashboard `takeaway`; `monitoring/terraform.tfstate` |

Do not create snapshots, extra disks or static IPs unless a later milestone
demonstrates a need. Record any addition in the inventory and cleanup procedure.
Reuse of an existing account resource must be explicit: teardown must not delete
resources owned by another project.

S3 state uses encryption, restricted access, versioning and locking. Bootstrap
initially needs local state before the bucket exists; migrate it to S3 once ready.
At final teardown, move bootstrap state back to a protected local location before
deleting its bucket. Never erase the only usable state while cleanup is incomplete.

## Monitoring and costs

One CloudWatch dashboard displays QA and prod side by side. Start with a small
set covering requests, errors, latency and server capacity; select exact signals,
retention and thresholds in D12–D14. Keep environment labels, avoid per-user or
per-request metric dimensions, and preserve existing log redaction.

The earlier $25–35/month estimate for both environments is a planning allowance,
not a quote. Confirm regional prices, service eligibility and credit expiry before
provisioning. Short runtime reduces server charges; retained resources can still
cost money. The user's $100 credit is not a spending cap.

## Complete teardown policy

1. Prevent new deployments and stop monitoring publishers/collectors so they
   cannot recreate log groups or continue sending data.
2. Remove alarms, notifications, dashboard, metric filters and log groups before
   removing the application servers.
3. Destroy QA/prod servers and their disposable data; release any allocated IPs,
   disks, keys and snapshots created for the project.
4. Remove project GHCR images/package as part of complete cleanup. Remove
   obsolete deployment secrets from GitHub through the appropriate owner.
5. Verify earlier cleanup succeeded, preserve bootstrap state locally, then remove
   every S3 object version/delete marker and the state bucket last.
6. Check the resource inventory for leftovers. If any deletion fails, retain state
   and finish cleanup before declaring teardown complete.

Exception to literal deletion of everything: CloudWatch does not offer deletion
of metric history. Stop publishing; retained metric data expires automatically
after 15 months. This is separate from deleting alarms, logs and dashboards.
See [AWS metric lifecycle documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html).

## Decisions to resolve before affected implementation

- Verify regional service availability
  and pricing for `eu-north-1` before provisioning.
- D5: configure Iftimie as production approver with self-approval allowed, while
  still requiring the explicit approval step. Restrict deployment branches.
- D7/D12: verify Lightsail/monitoring availability under the current account
  restrictions and settle CloudWatch publishing authentication. Verify the SSH
  server host key before deployment.
- D9: skipped at user request; HTTPS is out of scope.
- D12–D14: choose the small metric set, retention, thresholds and notification email.
- D16: an older image may not work with a newer database schema; rollback must
  document migration compatibility rather than promise automatic database reversal.

## Existing configuration implications

The current Compose file builds locally, publishes Nginx on localhost:8080 and
exposes PostgreSQL on localhost for developer tools. Later deployment configuration
must pull the approved image digest, expose web traffic appropriately and keep the
database internal. Current Nginx configuration is HTTP-only. No changes to these
files are part of D1.
