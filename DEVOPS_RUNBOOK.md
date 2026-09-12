# Local deployment tools (D3)

Region: `eu-north-1`. No AWS resources are created by these checks.
Current milestone status is in [DEVOPS_PROGRESS.md](DEVOPS_PROGRESS.md).

## Tools

AWS CLI sends commands to AWS. Terraform reads infrastructure configuration and
plans/applies changes; installing it does not create infrastructure.

On this Windows machine, tools are installed with Scoop:

```powershell
scoop install aws terraform
aws --version
terraform version
```

## Authentication

An existing `default` profile was found. Preserve it and use a separate profile
for this project. Never paste passwords, access keys, MFA codes or temporary
credentials into chat or commit them to Git.

This account uses AWS's new project-owner experience with Google sign-in.
The user confirmed Google MFA. CLI identity verification returned an assumed
`AccountFullAccessRole` session in the account matching the user's console,
not a root-user session. The earlier traditional IAM console-user instructions
did not apply to this experience. The manually created `alexandru-dev` IAM user
is unused by this setup; no access keys are needed for it.

Browser login (completed; repeat login when the session expires):

```powershell
aws configure set region eu-north-1 --profile takeaway-login
aws login --profile takeaway-login
```

The separate `takeaway` profile was configured using AWS's documented
credential-process mechanism. It obtains temporary credentials from
`takeaway-login`. These setup commands have already been run:

```powershell
aws configure set credential_process 'aws configure export-credentials --profile takeaway-login --format process' --profile takeaway
aws configure set region eu-north-1 --profile takeaway
```

In each new PowerShell terminal used for Terraform, select the profile:

```powershell
$env:AWS_PROFILE = 'takeaway'
$env:AWS_REGION = 'eu-north-1'
aws sts get-caller-identity --profile takeaway
```

The export command is executed internally by tools; do not run it standalone or
copy its output. `get-caller-identity` returns the account and identity, not secret
keys. Confirm they belong to the intended new account before resource creation.
It does not prove that all future deployment permissions are granted.

Repeat `aws login --profile takeaway-login` when the session expires. The
PowerShell environment settings above apply only to that terminal session.
Authentication/profile configuration lives in the user's `.aws` directory, outside
this repository. No Terraform infrastructure files are needed until D4.

D3 checks passed: AWS CLI 2.36.44, Terraform 1.16.2, resource-free Terraform console
expression, and STS identity through both profiles. Terraform AWS provider/backend
authentication will be exercised in D4; D3 did not initialize a provider or apply
infrastructure. AccountFullAccessRole is broad access, not least privilege.

Reference: [AWS CLI browser login and credential-process setup](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).

## Verify GitHub environment approvals (D5)

QA and prod environments were configured manually by the user. Both allow only
branch `main`; prod requires Iftimie approval, allows self-review and should disable
administrator bypass. These GitHub settings enforce the gate, not the workflow YAML.

After the reviewed workflow is committed and pushed to main:

1. Open Actions -> Check deployment approvals -> Run workflow, selecting main.
2. Confirm QA passes without approval and production shows Waiting for review.
3. Review deployments, select prod and approve; confirm the production job passes.

The workflow only prints messages and requests no token permissions or secrets.
If prod starts without approval, fix the environment settings before deployment
work. To verify the branch restriction, run the same workflow from a temporary
non-main branch containing it and confirm GitHub refuses environment access.
Do not weaken the environment rules to make that negative check pass.

The user monitors runs; do not poll unless requested. Live gate verification is
pending. AWS OIDC was removed from the plan; GHCR and SSH replace ECR/OIDC delivery.
