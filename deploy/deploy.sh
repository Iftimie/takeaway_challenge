#!/bin/bash
# Run from the deployment directory. Never resets or seeds the database.
set -euo pipefail
cd "$(dirname "$0")"
image=${1:?Usage: bash deploy.sh ghcr.io/iftimie/takeaway_challenge@sha256:DIGEST}
if [[ ! "$image" =~ ^ghcr\.io/iftimie/takeaway_challenge@sha256:[a-f0-9]{64}$ ]]; then
  echo 'Expected an immutable takeaway image digest.' >&2
  exit 1
fi
umask 077
if [ ! -f .env ]; then
  # Keep these values across redeployments: Postgres initializes its password once.
  {
    printf 'POSTGRES_DB=takeaway\nPOSTGRES_USER=takeaway\n'
    printf 'POSTGRES_PASSWORD=%s\n' "$(openssl rand -hex 32)"
    printf 'JWT_SECRET=%s\n' "$(openssl rand -hex 32)"
  } > .env.tmp
  mv .env.tmp .env
fi
export APP_IMAGE="$image"
compose=(docker compose --project-name takeaway-qa --env-file .env -f compose.yaml)
"${compose[@]}" pull
"${compose[@]}" up -d --wait db
# Always run migrations, including when Compose could reuse an exited container.
"${compose[@]}" run --rm --no-deps migrate
"${compose[@]}" up -d --no-deps --wait app
# Recreate Nginx so it resolves the current app container before its health check.
"${compose[@]}" up -d --no-deps --force-recreate --wait nginx
printf '%s\n' "$image" > current-image
echo 'QA deployment completed. Nginx listens on localhost:8080.'
