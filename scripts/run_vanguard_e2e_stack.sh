#!/usr/bin/env bash
# Sequential Vanguard E2E stack: API health, then Vite. Used by Playwright CI.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export ENVIRONMENT="${ENVIRONMENT:-development}"
export REDIS_REQUIRED="${REDIS_REQUIRED:-false}"
export VANGUARD_ANTIBOT_PROVIDER="${VANGUARD_ANTIBOT_PROVIDER:-none}"
export VANGUARD_APPLY_RATE_LIMIT="${VANGUARD_APPLY_RATE_LIMIT:-50}"

if [[ -n "${PYTHON:-}" ]]; then
  PY="$PYTHON"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="python3"
fi

"$PY" "$ROOT/scripts/run_vanguard_e2e_api.py" &
API_PID=$!
cleanup() {
  kill "$API_PID" 2>/dev/null || true
  wait "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ok=0
for _ in $(seq 1 45); do
  if curl -sf "http://127.0.0.1:8080/api/vanguard-site/v1/health" >/dev/null; then
    ok=1
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "Vanguard E2E API process exited before health check" >&2
    exit 1
  fi
  sleep 1
done
if [[ "$ok" != "1" ]]; then
  echo "Vanguard E2E API did not become healthy on :8080" >&2
  exit 1
fi

cd "$ROOT/src/web"
exec npm run dev -- --host 127.0.0.1 --port 5180
