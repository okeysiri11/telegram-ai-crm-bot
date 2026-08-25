#!/usr/bin/env bash
# Durable production deploy. Does NOT start Cloudflare Quick Tunnels.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is required for durable production deploy." >&2
  exit 1
fi

if [[ ! -f .env.production ]]; then
  echo "ERROR: .env.production is missing. Copy .env.example and fill real secrets." >&2
  exit 1
fi

if grep -Eq '^(POSTGRES_PASSWORD|GRAFANA_ADMIN_PASSWORD|IAM_JWT_SECRET)=(CHANGE_ME|postgres|admin|password)?$' .env.production; then
  echo "ERROR: .env.production still contains placeholder secrets." >&2
  exit 1
fi

if [[ ! -f src/web/dist/index.html ]]; then
  echo "Building production SPA…"
  npm ci --prefix src/web
  npm run build --prefix src/web
fi

export GIT_SHA="${GIT_SHA:-$(git rev-parse HEAD)}"
export SOURCE_REVISION="$GIT_SHA"

python3 scripts/production_doctor.py --offline
python3 scripts/validate_secrets_env.py

docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build

echo "Waiting for /liveness…"
for _ in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:8080/liveness" >/dev/null; then
    echo "DEPLOY_PRODUCTION=PASS revision=${GIT_SHA}"
    echo "Quick tunnels were not started. This is the durable compose path."
    exit 0
  fi
  sleep 3
done

echo "ERROR: /liveness did not become ready." >&2
exit 1
