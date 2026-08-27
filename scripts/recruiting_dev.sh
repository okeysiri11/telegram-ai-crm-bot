#!/usr/bin/env bash
# Reproducible Recruiting/Vanguard local startup.
# Starts Redis (Compose), then existing API :8080 and Vite :5180 if free.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="python3"
fi

echo "== Recruiting infra (Redis) =="
if ! "$ROOT/scripts/recruiting_infra.sh" start; then
  echo "Redis Compose did not start. Shared rate-limit/replay will stay process_local until Redis is healthy."
fi

echo "== Health =="
"$ROOT/scripts/recruiting_infra.sh" health || true

if lsof -nP -iTCP:8080 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "API already listening on :8080 — not starting a second backend."
else
  echo "Starting API scripts/run_api_local.py"
  nohup env REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}" "$PY" "$ROOT/scripts/run_api_local.py" >/tmp/ados-api-local.log 2>&1 &
  sleep 3
fi

if lsof -nP -iTCP:5180 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Vite already listening on :5180 — not starting a second frontend."
else
  echo "Starting Vite :5180"
  (cd "$ROOT/src/web" && nohup npm run dev -- --host 127.0.0.1 --port 5180 >/tmp/ados-vite-local.log 2>&1 &)
  sleep 2
fi

echo "== Verify =="
curl -sf "http://127.0.0.1:8080/api/recruiting-ops/v1/health" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print('sprint', d.get('sprint')); print('rate_limit_store', d.get('rate_limit_store')); print('replay_store', d.get('replay_store'))" || echo "API health not ready yet"
curl -sf -o /dev/null "http://127.0.0.1:5180/vanguard" && echo "frontend /vanguard OK" || echo "frontend not ready yet"
echo "Tracking worker runs in-process with the API (no separate process)."
echo "Logs: /tmp/ados-api-local.log  /tmp/ados-vite-local.log"
echo "Redis logs: scripts/recruiting_infra.sh logs"
