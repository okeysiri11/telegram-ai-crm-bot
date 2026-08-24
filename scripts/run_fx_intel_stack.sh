#!/usr/bin/env bash
# Sprint 50.3 — start Crypto FX stack (API :8080 + Vite :5180).
# Kills stale listeners for this stack, waits for HTTP 200, keeps logs, never silent-exit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_LOG="${ADOS_API_LOG:-/tmp/ados_api_50_5.log}"
WEB_LOG="${ADOS_WEB_LOG:-/tmp/ados_web_50_5.log}"
API_PID_FILE="${ADOS_API_PID:-/tmp/ados_api_50_5.pid}"
WEB_PID_FILE="${ADOS_WEB_PID:-/tmp/ados_web_50_5.pid}"
# keep legacy pid paths for stop compatibility
LEGACY_API_PID="${ADOS_API_PID_LEGACY:-/tmp/ados_api_50_1.pid}"
LEGACY_WEB_PID="${ADOS_WEB_PID_LEGACY:-/tmp/ados_web_50_1.pid}"

port_listening() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

listener_pid() {
  lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null | head -1
}

kill_tree() {
  local pid="$1"
  [[ -z "$pid" ]] && return 0
  if ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi
  local kids
  kids="$(pgrep -P "$pid" 2>/dev/null || true)"
  for c in $kids; do
    kill_tree "$c"
  done
  kill "$pid" 2>/dev/null || true
  sleep 0.3
  kill -9 "$pid" 2>/dev/null || true
}

reclaim_port_if_ours() {
  local port="$1"
  while read -r pid; do
    [[ -z "$pid" ]] && continue
    local cmd
    cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    case "$cmd" in
      *run_api_local.py*|*vite*|*npm\ run\ dev*|*/src/web*)
        echo "Reclaiming :$port PID $pid"
        kill_tree "$pid"
        ;;
      *)
        if [[ -n "$cmd" ]]; then
          echo "Port :$port occupied by foreign process PID $pid: $cmd"
          echo "FAIL occupied_port_$port"
          exit 1
        fi
        ;;
    esac
  done < <(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
}

wait_http() {
  local url="$1"
  local label="$2"
  local tries="${3:-90}"
  local i code
  code="000"
  for i in $(seq 1 "$tries"); do
    code="$(curl -s -m 2 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || echo 000)"
    if [[ "$code" == "200" ]]; then
      echo "OK  $label → HTTP $code"
      return 0
    fi
    sleep 1
  done
  echo "FAIL $label → last HTTP ${code:-000}"
  return 1
}

echo "== ADOS FX stack start (50.5) =="
echo "ROOT=$ROOT"
echo "Logs → $API_LOG | $WEB_LOG"

# Stop prior stack pid files (safe reclaim)
for f in "$API_PID_FILE" "$WEB_PID_FILE" "$LEGACY_API_PID" "$LEGACY_WEB_PID"; do
  if [[ -f "$f" ]]; then
    pid="$(cat "$f" 2>/dev/null || true)"
    echo "Stopping prior PID file $f → ${pid:-empty}"
    kill_tree "${pid:-}"
    rm -f "$f"
  fi
done

reclaim_port_if_ours 8080
reclaim_port_if_ours 5180
sleep 1

if port_listening 8080; then
  echo "FAIL :8080 still occupied after reclaim"
  exit 1
fi
if port_listening 5180; then
  echo "FAIL :5180 still occupied after reclaim"
  exit 1
fi

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "FAIL missing $ROOT/.venv/bin/python"
  exit 1
fi

echo "Starting API on :8080 …"
: >"$API_LOG"
if command -v setsid >/dev/null 2>&1; then
  setsid "$ROOT/.venv/bin/python" "$ROOT/scripts/run_api_local.py" >>"$API_LOG" 2>&1 </dev/null &
else
  nohup "$ROOT/.venv/bin/python" "$ROOT/scripts/run_api_local.py" >>"$API_LOG" 2>&1 </dev/null &
fi
echo $! >"$API_PID_FILE"
cp "$API_PID_FILE" "$LEGACY_API_PID" 2>/dev/null || true
cp "$API_PID_FILE" /tmp/ados_api_50_3.pid 2>/dev/null || true
disown || true
echo "API launcher PID $(cat "$API_PID_FILE") → $API_LOG"

echo "Starting frontend on :5180 …"
: >"$WEB_LOG"
(
  cd "$ROOT/src/web"
  if command -v setsid >/dev/null 2>&1; then
    setsid npm run dev -- --host 0.0.0.0 --port 5180 >>"$WEB_LOG" 2>&1 </dev/null &
  else
    nohup npm run dev -- --host 0.0.0.0 --port 5180 >>"$WEB_LOG" 2>&1 </dev/null &
  fi
  echo $! >"$WEB_PID_FILE"
  cp "$WEB_PID_FILE" "$LEGACY_WEB_PID" 2>/dev/null || true
  cp "$WEB_PID_FILE" /tmp/ados_web_50_3.pid 2>/dev/null || true
  disown || true
)
echo "Vite launcher PID $(cat "$WEB_PID_FILE") → $WEB_LOG"

echo "Waiting for HTTP readiness…"
api_ok=0
web_ok=0
wait_http "http://127.0.0.1:8080/health" "API /health" 90 && api_ok=1 || true
wait_http "http://127.0.0.1:5180/" "Frontend /" 90 && web_ok=1 || true
login_ok=0
crypto_ok=0
wait_http "http://127.0.0.1:5180/login" "Frontend /login" 30 && login_ok=1 || true
wait_http "http://127.0.0.1:5180/workspace/crypto" "Frontend /workspace/crypto" 30 && crypto_ok=1 || true

port_listening 8080 && listener_pid 8080 >"$API_PID_FILE" || true
port_listening 5180 && listener_pid 5180 >"$WEB_PID_FILE" || true
cp "$API_PID_FILE" "$LEGACY_API_PID" 2>/dev/null || true
cp "$WEB_PID_FILE" "$LEGACY_WEB_PID" 2>/dev/null || true

echo
echo "URLs:"
echo "  http://127.0.0.1:8080/health"
echo "  http://localhost:5180/"
echo "  http://localhost:5180/login"
echo "  http://localhost:5180/workspace/crypto"
echo "Logs: $API_LOG | $WEB_LOG"
echo "PIDs: API=$(cat "$API_PID_FILE" 2>/dev/null || echo ?) FE=$(cat "$WEB_PID_FILE" 2>/dev/null || echo ?)"
echo "Checks: api=$api_ok web=$web_ok login=$login_ok crypto=$crypto_ok"

if [[ "$api_ok" -eq 1 && "$web_ok" -eq 1 ]]; then
  echo "STACK READY"
  # stay attached briefly so nohup children are not tied to a dying interactive shell in some hosts
  sleep 1
  exit 0
fi

echo "STACK NOT READY — inspect:"
echo "  tail -80 $API_LOG"
echo "  tail -80 $WEB_LOG"
exit 1
