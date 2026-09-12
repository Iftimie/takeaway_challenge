# DevOps checkpoint

## Resume here

- Status: D1–D6 accepted. D7 in progress: QA server configuration drafted and
  mocked tests passed; no server created. Manual GitHub plan workflow drafted;
  QA AWS secret names verified. GitHub plan run and server creation still pending.
- Current design: [DEVOPS_DESIGN.md](DEVOPS_DESIGN.md). Region: `eu-north-1`.
  Repository: https://github.com/Iftimie/takeaway_challenge.
  D2 committed/pushed in 74bf7dc; user confirmed CI passed and waived the deliberate
  failure upload/download check. D4 applied with explicit user approval.
- Created state bucket takeaway-tfstate-455958489157-eu-north-1 and its safeguards.
  Bootstrap state is remote at bootstrap/terraform.tfstate. User has an account with
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
  Images use public GitHub Container Registry (GHCR), replacing ECR. GitHub publishes
  with its built-in token; servers pull without registry credentials. No AWS OIDC.
  User chose Terraform in Actions with dedicated IAM user keys in GitHub environment
  secrets. Bootstrap/teardown remain local using the takeaway profile.
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

- Verify the current AWS account allows Lightsail and the planned monitoring setup.
  Removing OIDC does not resolve unrelated service restrictions. No account upgrade
  or organization policy change is authorized by the revised deployment decision.
- GitHub prod approver confirmed: Iftimie, self-approval allowed. Still requires
  an explicit environment approval step. User reports settings configured; live
  gate verification succeeded per user confirmation.
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
| D2 | GitHub Actions Python/JS/browser tests with disposable PostgreSQL and failure artifacts. | Enable Actions if needed; push approved workflow or authorize push. | Passing CI run; report/trace verified locally; GitHub failure upload/download check waived by user. | Accepted by user; committed/pushed 74bf7dc |
| D3 | Check tooling and document local AWS/Terraform authentication. | Authenticate with AWS and enable MFA securely. | Correct AWS identity verified; Terraform runs locally. | Accepted by user; not committed |
| D4 | Bootstrap encrypted/versioned S3 state and locking; document deletion. | Review plan/cost and authorize first resource creation. | Remote state and locking work; state excluded from Git. | Accepted; committed f3bb61f, not pushed |
| D5 | Configure GitHub QA/prod environments, branch restrictions and approval gate. | Iftimie approver confirmed; complete restricted GitHub settings. | QA can proceed; prod waits for explicit approval; allow Iftimie self-approval. | Accepted by user; committed/pushed 75ba1c3 |
| D6 | Publish commit-identified Docker images to public GHCR; document retention/cleanup. | Trigger/push approved workflow; set package visibility if needed. | Passing build publishes a recorded digest; anonymous image pull works. | Accepted by user; committed/pushed 43c67dd |
| D7 | Reusable Lightsail Terraform, QA networking, Docker bootstrap and SSH deployment access. | Review plan/cost; generate/store SSH private key securely. | QA server starts; deployment access works; database not public. | In progress: plan ready; awaiting server creation approval |
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

- D7 checkpoint committed/pushed as 0dfc332; plan run 34698405042 failed during
  validation after AWS identity and S3 backend initialization passed. The Windows
  lockfile lacked the Linux unpacked-provider checksum with read-only init.
  Ran providers lock for windows_amd64 and linux_amd64 against HashiCorp-signed
  packages; added the Linux checksum without changing AWS provider 6.64.0.
  Fix awaits commit/push and remote rerun; no server created.

- D7: Lightsail APIs list eu-north-1, ubuntu_24_04 and small_3_0 Linux IPv4
  bundle at $12/month; no existing instances. Init/validate and 2 mocked tests pass
  in infra/server. QA state backend configured; no real server plan/apply yet.
- Generated RSA 4096 QA key outside repo at C:/Users/Alexandru/.ssh/takeaway_qa;
  non-interactive use verified and private file ACL restricted. Never print contents.
  GitHub CLI 2.100.0 authenticated as Iftimie; uploaded qa SSH_PRIVATE_KEY from stdin
  and verified secret name. Private key contents never displayed.
- User configured github-actions-qa credentials with custom QA policies. Verified
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and SSH_PRIVATE_KEY secret names only;
  credential values and effective IAM policies have not been inspected.
  Uploaded SSH_PUBLIC_KEY as a QA environment variable. Added manual plan-qa.yml,
  main-only, serialized, pinned Terraform version, QA backend and no apply step.
  This checks auth/backend access before attempting billable creation; a passing
  plan does not prove creation permissions. Remote run awaits push authorization.
  Local verification: Terraform format/validate passed, 2 mocked tests passed,
  Git whitespace check passed. Python YAML parsing unavailable (PyYAML not installed);
  workflow execution validation remains pending in GitHub. No dependency installed.
- Previously detected current public IPv4 for /32 SSH restriction;
  saved qa.tfplan: 3 add (instance, public key, firewall), 0 change, 0 destroy.
  No apply. Live cloud-init/SSH verification pending. No D7 commit/push.

- D6: Tests workflow exports the tested image only on main after success; a separate
  packages:write job loads/tags/pushes to GHCR using GITHUB_TOKEN and records digest.
  Added Docker source label. Image transfer artifact retained one day.
- Full Docker/Nginx browser suite: 16 passed in 55.7s. Docker export/load preserved
  image ID; temporary archive removed. Diff whitespace check passed.
- D6 committed/pushed 43c67dd. User reported workflow finished and package public.
  Pulled full commit-SHA tag using a fresh empty Docker config (no registry credentials).
  Published reference: ghcr.io/iftimie/takeaway_challenge@sha256:d8f3547788685601d83c285351b20b86ec2efbe1cf7b58201d971200a8b06b83
- Documented manual obsolete-version cleanup retaining deployed/rollback digests.
  No deployment. No Python/JS feature changes.

- D5: user reports qa/prod environments configured. Added manual-only
  check-environments.yml: QA prints confirmation, dependent prod job uses GitHub's
  approval gate. No checkout, secrets, AWS access or deployment. Pushed as 75ba1c3.
- Initial run did not pause; user corrected environment settings and confirmed
  the approval gate then worked. Non-main branch rejection not separately tested.

- User approved removing AWS OIDC and proceeding with SSH deployment. Design and
  D5/D6 scope updated to GHCR, local Terraform and GitHub environment approval.
  No workflows, GitHub settings or AWS resources changed for this decision.

- D5 read-only IAM OIDC enumeration denied by an organization SCP, despite the
  AccountFullAccessRole session. No retry using another identity or policy changes.
  GitHub CLI not installed; no GitHub settings modified. Iftimie approver confirmed.
- AWS documents advanced-feature activation as irreversible, transferring governance
  to the user and removing spend limits. Review before proceeding:
  https://docs.aws.amazon.com/accounts/latest/reference/activate-advanced-features.html

- D4: init, validate and mocked security test passed (1 run). Approved apply created
  6 resources (one bucket and five configurations). Activated backend.tf and migrated
  local state to S3. Local state backups remain ignored; provider lockfile retained.
- Bucket: takeaway-tfstate-455958489157-eu-north-1. SSE-S3 encryption, versioning,
  blocked public access, disabled ACLs, HTTPS-only policy. Native S3 locking enabled.
- Verified AWS bucket settings and encrypted/versioned remote state. A paused
  output-only apply blocked a competing plan with Error acquiring the state lock.
  Cancelled verification apply, removed temporary output, final plan: no changes.
- State/plans/providers ignored by Git; provider dependency lockfile retained.
  Documented migration and bucket-last deletion. D4 committed as f3bb61f; not pushed.

- D3: installed AWS CLI 2.36.44 and Terraform 1.16.2 through Scoop; download hashes
  passed. Both version commands passed; Terraform console evaluated `1 + 1` as 2.
- User uses the new AWS project-owner experience with Google MFA, not traditional
  root login. STS verified AccountFullAccessRole in the account matching the console.
- User authenticated takeaway-login; configured takeaway credential-process profile
  and verified identical STS identity and eu-north-1 region. Default profile preserved.
- DEVOPS_RUNBOOK.md corrected for the actual sign-in flow. alexandru-dev IAM user
  was created manually during setup but is unused; no assistant deletion performed.
- No AWS infrastructure created. Terraform AWS provider/backend verification belongs
  to D4; D3 checked CLI identity/profile and Terraform executable. No D3 commit/push.

- D2 local verification: UI build passed; Python 405 passed (two existing dependency
  deprecation warnings); JavaScript 45 passed; Docker/Nginx browser suite 16 passed
  in 55.1s with CI reporting enabled. Python used the disposable browser-test DB.
- Temporary deliberate browser failure generated HTML/video/trace; trace archive
  integrity checked. Temporary test removed before the passing full run.
- Git diff whitespace check passed. README documents CI triggers and artifact viewing.
- D1/D2 committed and pushed as 74bf7dc. User confirmed all GitHub tests passed.
  User waived deliberate failure artifact upload/download verification; this check
  was not performed. Local failure report/trace verification above remains valid.
- No AWS creation or deployment. Python dependency ranges remain unpinned;
  no dependency changes made in D2.
