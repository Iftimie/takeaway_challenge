# QA deployment (D8)

Copy this directory to `/opt/takeaway` on QA, then run `bash deploy.sh IMAGE`,
using the immutable GHCR digest from the successful publishing job. Deployment
is manual in D8; GitHub deployment automation comes in D10.

The script generates `.env` with random database/JWT secrets on its first run.
It preserves that file and the named PostgreSQL volume on subsequent runs.
Never delete `.env` while keeping the database volume. Secret values are not
printed, sent to GitHub, or stored in Terraform. `current-image` records the last
successfully started image. A failed migration stops deployment; migrations are
not automatically rolled back. This simple deployment can briefly interrupt requests.

No host database port is published. Until D9 adds HTTPS, Nginx is localhost-only.
On your computer, keep this tunnel running (substitute the QA IP):

```powershell
ssh -i "$env:USERPROFILE\.ssh\takeaway_qa" -L 8081:127.0.0.1:8080 deploy@QA_IP
```

Open http://localhost:8081/ui/ in your browser.

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
demo accounts with password `password`. Use only for disposable QA data behind
the SSH tunnel. It is never part of deployment. Before exposing QA publicly,
replace demo credentials or recreate an empty database.

Check deployment with `docker compose -p takeaway-qa ps` and
`curl --fail http://127.0.0.1:8080/health`. Verify redeployment preserves a record
through the API; a health response alone does not test persistence.

Run the isolated local persistence test from the repository (substitute IMAGE
with the published digest; Docker must be running):

```powershell
$env:DOCKER_CONTEXT = 'desktop-linux'
.\.venv\Scripts\python.exe scripts/test_deployment.py IMAGE
```

It uses port 8768 and a dedicated `takeaway-d8-test` Compose project, then removes
that test project's containers and volume. It does not touch the development DB.
