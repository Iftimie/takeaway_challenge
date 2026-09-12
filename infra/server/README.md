# QA server (D7)

One Ubuntu 24.04 Lightsail instance, small_3_0 (2 GB RAM, IPv4), in eu-north-1a.
The catalog lists $12/month; short sessions are billed by runtime subject to AWS
terms. No static IP, extra disk, snapshot or production instance is included.

The qa backend stores state separately from bootstrap.

## GitHub plan

After this workflow is pushed to main, open Actions -> Plan QA infrastructure ->
Run workflow. Supply your public IPv4 followed by /32. The workflow uses the qa
environment's AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY secrets and
SSH_PUBLIC_KEY variable. The private SSH key is not needed for planning.

It checks the AWS account, initializes the existing S3 backend, validates/tests
the configuration and prints a plan. It does not apply changes. Review the
Plan QA resources step; the first plan should propose three resources. A successful
plan checks authentication and backend access, but does not prove that AWS allows
all creation operations. GitHub execution is pending the first push/run.

## Local commands

When updating the provider lockfile, record both development and CI platforms:

```powershell
terraform '-chdir=infra/server' providers lock -platform=windows_amd64 -platform=linux_amd64
```

For local inspection and eventual teardown, use AWS_PROFILE=takeaway.
Set TF_VAR_ssh_public_key from ~/.ssh/takeaway_qa.pub and TF_VAR_ssh_cidr to your
current public IPv4 plus /32, then:

```powershell
terraform '-chdir=infra/server' init '-backend-config=qa.s3.tfbackend'
terraform '-chdir=infra/server' plan '-out=qa.tfplan'
# Only after reviewing and approving the creation plan:
terraform '-chdir=infra/server' apply qa.tfplan
```

Only the public key enters Terraform. The private key is stored outside the repo
and uploaded to GitHub's qa environment as SSH_PRIVATE_KEY. Never commit it.
The saved plan is ignored by Git and contains the planned IP restriction.

Cloud-init installs Ubuntu's Docker/Compose packages and creates deploy with access
to Docker and /opt/takeaway. Docker group membership effectively grants host-level
control; this is a dedicated QA key, not a command-restricted deployment credential.
The Ubuntu administrative account also uses this key. Password SSH login is disabled.

Only SSH from the configured /32 is exposed. Web ports and GitHub runner access
are later deployment steps. No app or database containers are started in D7.
On creation, verify cloud-init completion, Docker/Compose versions, deploy login
and firewall rules. Verify SSH host identity using an independent AWS console
channel before trusting the first SSH connection. A real server has not yet been
created or checked. IPs can change on stop/start without a static IP.

Reuse this configuration for prod only with a separate backend, key and environment
value in its milestone. Do not switch the QA backend to prod or reuse its state.
