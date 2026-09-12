# Terraform state bootstrap (D4)

Creates one S3 bucket in eu-north-1 for account 455958489157. Terraform shows six
resources because versioning, encryption, ownership, public-access blocking and
the HTTPS-only policy are configured separately from the bucket itself.

Use the `takeaway` AWS profile from DEVOPS_RUNBOOK.md. No credentials are stored
here. `allowed_account_ids` prevents applying this configuration in another account.
The provider lockfile is committed; local state, downloaded providers and saved
plans are excluded from Git.

## First creation

D4 creation and migration are complete; backend.tf is active. For the existing
bucket, use ordinary `terraform init` and `terraform plan`. The first-creation
procedure below is for recreation after full teardown: move backend.tf outside
the directory before initializing local state. Do not do this while remote state
still manages live resources.

Run from the repository root in PowerShell:

```powershell
$env:AWS_PROFILE = 'takeaway'
$env:AWS_REGION = 'eu-north-1'
terraform '-chdir=infra/bootstrap' init
terraform '-chdir=infra/bootstrap' validate
terraform '-chdir=infra/bootstrap' test
terraform '-chdir=infra/bootstrap' plan '-out=bootstrap.tfplan'
```

Review the plan and cost before applying. The initial backend is local because
the bucket does not yet exist. Only after approval:

```powershell
terraform '-chdir=infra/bootstrap' apply bootstrap.tfplan
Copy-Item infra/bootstrap/backend.tf.example infra/bootstrap/backend.tf
terraform '-chdir=infra/bootstrap' init -migrate-state
```

Accept the migration prompt after confirming its destination. Retain local state
backups until the remote state is verified. Commit the activated backend.tf so
subsequent checkouts use remote state. Backend configuration contains no secrets.

The backend stores bootstrap/terraform.tfstate and uses S3's native .tflock object.
Other milestones will use separate shared/, qa/, prod/ and monitoring/ state keys.
No empty environment directories or DynamoDB lock table are created now.

## Verification after creation

Check bucket versioning, encryption, ownership controls, public-access block and
policy through the AWS CLI. Run a new plan and expect no changes. Verify the state
object exists remotely and is encrypted. Exercise two competing Terraform commands
against the same state: the second must fail to acquire the lock while the first
holds it, then succeed once released. Do not disable locking or force-unlock an
active operation. The mocked test covers configuration safeguards, not live locking.

## Costs and complete deletion

Live verification passed: bucket safeguards and encrypted/versioned state object;
an apply paused at confirmation blocked a competing plan with a state-lock error.
The output-only verification apply was cancelled, its temporary configuration
removed, and a subsequent plan returned no changes. No force-unlock was needed.

S3 Standard charges for stored data (including previous versions), requests and
applicable transfer; there is no minimum charge. Small state files and occasional
Terraform runs should cost only cents, but this is a planning estimate, not a cap
or a verified regional quote. Credit eligibility is not assumed. No paid KMS key,
server or database is introduced. See https://aws.amazon.com/s3/pricing/.

Destroy this bucket LAST, after all other state groups have been successfully
destroyed. Stop all Terraform writers, replace the S3 backend block with a local
backend and run `terraform init -migrate-state` to preserve bootstrap state locally.
Verify that local state lists the managed resources before deleting remote objects.
Empty all versions and delete markers from this exact bucket (ordinary `s3 rm`
does not remove version history), then review/apply a bootstrap destroy plan.
`force_destroy=false` makes an ordinary destroy fail while the bucket is nonempty.
Retain the local state if any cleanup fails. The destructive rehearsal is D15.

References: https://developer.hashicorp.com/terraform/language/backend/s3
