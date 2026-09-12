# Two-environment pipeline

Only two GitHub environments and two IAM users are used: qa and prod.
Their AWS credential secrets and SSH_PUBLIC_KEY variables are already configured.
Terraform does not use the SSH_PRIVATE_KEY secrets; server login/deployment will.

| Event | Pipeline |
|---|---|
| PR opened, reopened or updated against main | Python/JS/browser tests; QA Terraform plan |
| PR merged into main | Tests and image publishing; fresh QA plan/apply when needed; QA app deployment/smoke checks; production approval; fresh prod plan/apply |
| PR closed without merging or push without a PR | No automatic pipeline |

Post-merge execution uses push on main, not the pull_request closed event, so
production deployment uses the main ref. A small initial check verifies that the
commit matches a merged PR; a direct main push without a matching merge stops there.

Terraform jobs run only for changes under infra/server/ or .github/. Fork PRs run
tests and credential-free Terraform validation; authenticated QA planning is skipped.
Same-repository PRs use the existing QA credentials, including their write permissions.
The manual QA plan remains available. Teardown stays local.

## GitHub settings

- qa: no reviewer; allowed deployment branch patterns main and refs/pull/*/merge.
- prod: main only; Iftimie approval required, self-approval allowed.

The user requested removal of qa-plan and prod-plan; both were deleted.
Automatic approval review blocked the agent from adding the PR-ref pattern to QA.
The user subsequently configured it manually and supplied a screenshot confirming
main and refs/pull/*/merge. No production setting was changed.

## Approval and apply

Review the QA plan from the PR check logs/summary. Merging an infrastructure PR
starts billable QA creation. The merge run generates a fresh QA plan, then applies
that file. It does not reuse the PR plan.

The prod environment approval gates the entire production job: after approval it
generates and immediately applies a fresh saved plan on the same runner. There is
no second approval between prod plan and apply. Approval authorizes the production
run, not a previously generated prod plan. No binary plan is uploaded to S3 or GitHub.
S3 still stores separate QA/prod Terraform state and lock files.

Merged runs are serialized, including the approval wait. QA jobs share the
terraform-qa concurrency group with manual planning. S3 locking protects state
during each Terraform operation. If main changes while approval is pending, the
production job stops; run the latest appropriate merged-PR workflow and approve
again. Preserve state after failures; partial resources may exist and incur charges.

QA application deployment runs for every verified merged PR after publishing,
including application-only changes where Terraform is skipped. It copies the
small deployment bundle over SSH and uses the immutable digest returned by the
publishing job. Health and UI checks use QA's public HTTP address. Failure prevents
production infrastructure promotion. Production application deployment remains D11.

QA uses existing AWS/SSH secrets plus SSH_KNOWN_HOSTS, a public variable containing
AWS-verified host keys under alias takeaway-qa. It is configured for the current
server. If Terraform recreates QA, refresh this variable using host keys returned
by the authenticated Lightsail get-instance-access-details API before redeploying.
A changed key fails closed; do not disable host verification or blindly trust a scan.

Merged runs remain serialized by the existing pipeline concurrency group. Manual
local deployments should not run alongside Actions. No sample reset runs in CI.
The existing database volume and server-generated secrets remain in place.
