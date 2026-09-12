# PR infrastructure pipeline

## What runs

| Event | Jobs |
|---|---|
| PR opened, reopened, or updated against main | Python, JavaScript and browser tests; Terraform validation for infrastructure changes; QA plan for same-repository PRs |
| PR merged into main | Repeat tests for merged code and publish the tested image; fresh QA plan/apply; prod plan; production approval; apply the saved prod plan |
| PR closed without merging | No tests or infrastructure changes |
| Ordinary branch push without a PR | No automatic pipeline |

Terraform runs only when the PR changes infra/server/ or .github/ (including a
rename out of those paths). App-only PRs still run tests and publish after merge.
The existing manual QA plan is available for troubleshooting. There is no manual
apply or destroy workflow. Local teardown remains available.

This change provisions servers only. Application deployment, database setup,
SSH/bootstrap verification and QA smoke tests are not implemented by this pipeline.
QA apply success currently gates prod planning; it is not an application health check.

## GitHub setup before merge

Every environment below needs AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY secrets,
and an SSH_PUBLIC_KEY variable for its target server. Never put private keys in
variables. Use separate QA and prod SSH keys; prod-plan and prod use the same prod
public key. SSH_PRIVATE_KEY is not used by Terraform.

| Environment | AWS identity | Allowed deployment refs | Approval |
|---|---|---|---|
| qa-plan | Dedicated planning user with iam/qa-plan.json | refs/pull/*/merge | None |
| qa | Existing QA infrastructure user | main | None |
| prod-plan | Dedicated planning user with iam/prod-plan.json | main | None |
| prod | Dedicated production infrastructure user | main | Iftimie; self-approval allowed |

The planning policies allow reading Lightsail metadata in Stockholm and their own
state, plus creating/deleting the state lock. They cannot create or delete servers,
or write Terraform state. prod-plan additionally writes saved plans to private S3.
These JSON policies are drafts checked locally, not yet exercised with those users.
Organization restrictions still apply.

For prod apply, use production equivalents of the two QA apply policies previously
provided: replace QA state paths and Environment=qa conditions with prod. It also
needs s3:GetObject and s3:DeleteObject on:

```text
arn:aws:s3:::takeaway-tfstate-455958489157-eu-north-1/prod/plans/*
```

Do not attach QA write credentials to qa-plan. The existing qa environment remains
main-only. No environment settings were changed by this PR: automatic approval
review rejected widening qa to PR refs, so planning has its own identity instead.
Missing credentials cause a visible job failure, not a skipped successful plan.

PR jobs use pull_request, never pull_request_target. Fork PRs get tests and
credential-free Terraform validation; their authenticated QA plan is skipped.
Same-repository branches are trusted to run with planning credentials. Import a
fork's changes into a reviewed, trusted branch if an authenticated plan is needed.

## Reviewing and applying

1. Open the QA plan job summary from the PR checks and review the proposed changes.
2. Merge only after tests/planning pass and production credentials are configured.
   Merging an infrastructure PR authorizes billable QA creation.
3. The merged-code run creates a new QA plan and applies it. The PR plan is not reused.
4. Review the prod-plan job summary, which identifies the commit and shows changes.
5. Approve the prod environment. The apply job downloads exactly that saved plan,
   checks its SHA-256 digest and applies it without re-planning.

The binary prod plan stays in the existing private S3 bucket, not a public GitHub
artifact. Each run/attempt has a different object key. After successful apply the
object is deleted, but bucket versioning retains older versions until final cleanup.
Cancelled/rejected/failed runs can leave plan objects; delete all their versions
during the existing bucket-last teardown. Plan text in GitHub summaries is visible
with the public workflow logs; sensitive Terraform values must remain marked sensitive.

Merged release runs are serialized, including the production approval wait. PR
planning and QA apply also share the terraform-qa lock with manual planning.
GitHub can replace an older pending run with a newer pending run. Terraform S3 locks
protect state during each operation, including against local Terraform commands.

If main advances while production approval is pending, prod apply stops rather than
deploying old code. Run the latest appropriate merged-PR workflow from the Actions
UI to generate a fresh plan and obtain approval again. A stale Terraform state also
causes apply to fail. After any partial failure, preserve state and rerun the whole
appropriate workflow so it plans the actual remaining changes; do not blindly retry
the old saved-plan apply job. Approval rejection does not roll back the QA server.

Branch protection/required checks are separate repository settings. This PR does
not configure them or merge itself. Direct pushes to main do not trigger this pipeline.
