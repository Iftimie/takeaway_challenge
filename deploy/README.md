# QA deployment (D8)

Copy this directory to `/opt/takeaway` on QA, then run `bash deploy.sh IMAGE`,
using the immutable GHCR digest from the successful publishing job. Deployment
is now automatic after a verified PR merge (D10). The same script remains
available for local debugging. Do not run it concurrently with Actions.

The script generates `.env` with random database/JWT secrets on its first run.
It preserves that file and the named PostgreSQL volume on subsequent runs.
Never delete `.env` while keeping the database volume. Secret values are not
printed, sent to GitHub, or stored in Terraform. `current-image` records the last
successfully started image. A failed migration stops deployment; migrations are
not automatically rolled back. This simple deployment can briefly interrupt requests.

No host database port is published. Nginx publishes port 80 on the server's public
IPv4 address. Open `http://QA_IP/ui/` directly; no SSH tunnel is needed.
HTTP is unencrypted until D9 adds HTTPS. Use disposable challenge credentials.
Terraform opens port 80 on both QA and prod; prod has no app until its deployment
milestone. Opening a firewall port does not deploy the application.

On the server, prepare subsequent Compose commands with:

```bash
cd /opt/takeaway
export APP_IMAGE=$(cat current-image)
```

Create your admin interactively; choose its password at the hidden prompt:

```bash
docker compose -p takeaway-qa run --rm --no-deps app python -m app.create_admin --email YOUR_EMAIL --name YOUR_NAME
```

Optional sample data uses the existing repository script. Copy
`scripts/reset_demo_db.py` into `/opt/takeaway/reset_demo_db.py`, then explicitly run:

```bash
docker compose -p takeaway-qa run --rm --no-deps -v "$PWD/reset_demo_db.py:/app/reset_demo_db.py:ro" app python /app/reset_demo_db.py --yes-delete-all-data
```

This deletes every application record, including an existing admin, and creates
demo accounts with password `password`. Use only for disposable QA data on QA. It is never part of deployment. Do not use real credentials or personal data in this HTTP demo.

Check deployment with `docker compose -p takeaway-qa ps` and
`curl --fail http://127.0.0.1/health`. Verify redeployment preserves a record
through the API; a health response alone does not test persistence.

Run the isolated local persistence test from the repository (substitute IMAGE
with the published digest; Docker must be running):

```powershell
$env:DOCKER_CONTEXT = 'desktop-linux'
.\.venv\Scripts\python.exe scripts/test_deployment.py IMAGE
```

It uses port 8768 and a dedicated `takeaway-d8-test` Compose project, then removes
that test project's containers and volume. It does not touch the development DB.


## Production (D11)

GitHub Actions deploys after QA smoke checks and the existing prod environment
approval. Both environments receive the same published image digest. Production
runs on its own server with Compose project `takeaway-prod`, its own PostgreSQL
volume, and first-run server-generated secrets. No database or sample data is copied.

Before the first merge, set prod's `SSH_KNOWN_HOSTS` variable with the verified
production host keys (alias `takeaway-prod`). On the current development computer,
the previously AWS-verified keys have been prepared in an ignored local file:

```powershell
Get-Content ci-results/prod-pinned-hosts -Raw | gh variable set SSH_KNOWN_HOSTS --env prod --repo Iftimie/takeaway_challenge
```

If the server has been recreated since verification, obtain and verify its new
keys first. Existing prod AWS and SSH secrets remain in use.

After merging, wait for QA, approve production, then open the production URL in
the job summary. Confirm the QA and prod image digests match. Initial production
has no admin or sample data. Later admin creation uses the existing interactive
command with `-p takeaway-prod` on the production server.

Manual debugging uses `bash deploy.sh IMAGE prod`; omitting the environment
preserves the earlier QA default. Normal deployment happens only in Actions.
Terraform runs only when infrastructure/workflow files change; app-only merges
still deploy to both environments. Migration rollback is not automatic.
