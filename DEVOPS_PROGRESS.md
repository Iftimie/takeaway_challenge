# DevOps checkpoint

## Resume here

- Status: D1 accepted; D2 implemented locally, awaiting review and GitHub verification.
- Current design: [DEVOPS_DESIGN.md](DEVOPS_DESIGN.md). Region: `eu-north-1`.
  Repository: https://github.com/Iftimie/takeaway_challenge.
  Current: D2. User authorized committing/pushing the current changes and will
  report the GitHub run result; do not poll it. GitHub verification remains pending.
- No AWS resources created by the assistant. User has a new AWS account with
  $100 credit; credit eligibility/expiry and service access must be checked.
- Work on one milestone at a time. Verify relevant code, keep changes small,
  record actual checks, then stop for review. Commit/push only when requested.
- Keep this file concise: update current state and the milestone row; retain
  only useful decisions, verification and limitations, not tool logs.
- Use this file for DevOps continuity. PROGRESS.md contains the older app/UI history.

## Agreed decisions

- AWS Lightsail + Docker Compose: separate QA and prod instances, each running
  Nginx, FastAPI/Uvicorn with built Vue UI, and PostgreSQL. Start with 2 GB RAM
  per instance, subject to final cost review. Region: `eu-north-1` (user selected).
- Short-lived development/demo environments, typically 1–2 days. Both databases
  are disposable. No high availability requirement for this challenge.
- GitHub repository will be public. Pipeline: tests -> publish versioned image ->
  QA deployment/smoke checks -> manual approval -> same image digest to prod.
- Python/JS/browser tests run against disposable test data, never deployed prod.
- SSH deployment with separate QA/prod keys held in GitHub environment secrets.
  AWS access from GitHub uses OIDC; no permanent AWS keys in repository secrets.
- Terraform manages resources. Private encrypted/versioned S3 backend with
  locking and separate QA/prod state. Bootstrap resources are separate.
- No purchased domain. Trusted HTTPS using IP certificates with automated
  issuance/renewal; verify client support and AWS setup at implementation time.
- One CloudWatch dashboard showing both environments. Small metric set, bounded
  log retention, environment-specific alarms and email notifications.
- Complete teardown: alarms/monitoring before applications; remove databases,
  disks, IPs, images, logs, snapshots if any, and other created resources. Delete
  every state object version and the state bucket last, after successful cleanup.
  Check for leftovers. Keep state available if cleanup fails; do not erase it early.
- Seed sample data explicitly after recreation, never during ordinary deployment.
- Lightsail selected for minimal Terraform/setup complexity and reuse of Compose.
  Trade-off: self-managed servers/PostgreSQL and one failure point per environment.
- Earlier continuous-use estimate: $25–35/month for both Lightsail environments;
  only a planning estimate, not a quote. Short runs reduce runtime charges, but
  retained resources may still cost money. No assumption that credits cover all.

## Open inputs / decisions

- Actual GitHub environment approval settings.
- Production approver; a sole operator must not enable a self-approval ban that
  prevents all production deployments.
- AWS authentication, billing alerts, SSH key setup, QA/prod secrets, certificate
  contact email if required, alarm email/subscription confirmation.
- Exact resources/pricing, metrics/thresholds and retention to review in their
  milestones. No sensitive values belong in this file, chat or Git.

## Milestones

Update each status explicitly: in progress, implemented
awaiting review, accepted, committed (hash). Recording this plan is not completion
of D1 and does not authorize creating AWS resources.

| ID | Assistant work | User action/input | Acceptance criteria | Status |
|---|---|---|---|---|
| D1 | Record architecture, resource ownership/naming and teardown policy. | Confirm region; provide public repo URL (both supplied). | Agreed resource list/lifecycle; no resources created. | Accepted 2026-09-12; not committed |
| D2 | GitHub Actions Python/JS/browser tests with disposable PostgreSQL and failure artifacts. | Enable Actions if needed; push approved workflow or authorize push. | Passing CI run and inspectable failed-test report/trace. | Implemented locally, awaiting review; GitHub verification pending |
| D3 | Check tooling and document local AWS/Terraform authentication. | Authenticate with AWS and enable MFA securely. | Correct AWS identity verified; Terraform runs locally. | Not started |
| D4 | Bootstrap encrypted/versioned S3 state and locking; document deletion. | Review plan/cost and authorize first resource creation. | Remote state and locking work; state excluded from Git. | Not started |
| D5 | GitHub OIDC/scoped AWS roles and QA/prod environments/approval gate. | Choose approver; complete restricted GitHub settings. | Intended role assumption works; prod waits for approval. | Not started |
| D6 | Publish commit-identified Docker images to ECR with retention policy. | Trigger/push approved workflow. | Passing build publishes a recorded image digest. | Not started |
| D7 | Reusable Lightsail Terraform, QA networking, Docker bootstrap and SSH deployment access. | Review plan/cost; generate/store SSH private key securely. | QA server starts; deployment access works; database not public. | Not started |
| D8 | Deploy QA Compose stack, migrations, secrets and explicit sample-data setup. | Supply QA secrets/admin credentials securely. | QA works; app redeploy preserves DB; seeding is separate. | Not started |
| D9 | IP-certificate issuance/renewal and HTTPS configuration. | Certificate contact email if needed. | Trusted QA HTTPS and verified renewal procedure. | Not started |
| D10 | Automatic QA deployment after successful CI, smoke checks and deployment serialization. | Merge/push approved change. | Tested image deployed to QA; clear failure/success result. | Not started |
| D11 | Separate prod instance/database/secrets; promote QA image after approval. | Set prod secrets; approve first deployment. | Isolated prod, identical approved digest, HTTPS/smoke checks pass. | Not started |
| D12 | Bounded CloudWatch logs and agreed metrics labelled by environment. | Review metric set and retention. | QA/prod activity distinguishable; errors searchable by request ID. | Not started |
| D13 | Single Terraform-managed dashboard for QA and prod. | Review usefulness during a demo. | Traffic/errors/latency/resources clearly visible for both. | Not started |
| D14 | Environment-specific alarms and controlled failure/recovery checks. | Supply email and confirm AWS subscription. | Understandable failure notification and recovery verified. | Not started |
| D15 | Ordered complete teardown and recreation rehearsal, including bootstrap/state cleanup. | Authorize destructive rehearsal; confirm disposable data. | No remaining created billable resources; successful recreation. | Not started |
| D16 | Failed deployment and previous-image rollback rehearsal; final runbook. | Review final operations demo. | Deploy/approve/recover/clean up demonstrated; migration rollback limits documented. | Not started |

## Relevant existing implementation

- compose.yaml, Dockerfile, nginx/default.conf: current local deployment.
- playwright.config.js, compose.browser-tests.yaml, tests/browser_db.py: isolated
  browser tests; UI_TEST_COMPOSE=1 tests through Docker/Nginx. Docker context defaults
  to desktop-linux on Windows and the active context on Linux; DOCKER_CONTEXT overrides.
- .github/workflows/tests.yml: one Ubuntu test job, read-only repository permission,
  disposable DB, full-stack browser tests, cleanup and seven-day failure artifacts.
- npm run test:unit, npm run test:browser, npm run test:demo; demo keeps a trace.
- scripts/reset_demo_db.py: destructive local sample-data reset; must never be
  invoked automatically by production CI/CD.
- Existing log middleware redacts declared sensitive fields; inspect before
  forwarding logs and decide a small metric set rather than adding a large stack.
- Backend dependency ranges are not fully locked; review reproducibility in CI.

## Latest verification

- D2 local verification: UI build passed; Python 405 passed (two existing dependency
  deprecation warnings); JavaScript 45 passed; Docker/Nginx browser suite 16 passed
  in 55.1s with CI reporting enabled. Python used the disposable browser-test DB.
- Temporary deliberate browser failure generated HTML/video/trace; trace archive
  integrity checked. Temporary test removed before the passing full run.
- Git diff whitespace check passed. README documents CI triggers and artifact viewing.
- Not yet verified on a GitHub Linux runner: workflow execution and artifact upload/
  download. No commit, push, AWS creation or deployment. Python dependency ranges
  remain unpinned; no dependency changes made in D2.
