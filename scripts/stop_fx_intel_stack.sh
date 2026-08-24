#!/usr/bin/env bash
# Sprint 50.3 — stop API (:8080) and Vite (:5180) for this project stack only.
set -euo pipefail

API_PID_FILE="${ADOS_API_PID:-/tmp/ados_api_50_5.pid}"
WEB_PID_FILE="${ADOS_WEB_PID:-/tmp/ados_web_50_5.pid}"
LEGACY_API_PID="${ADOS_API_PID_LEGACY:-/tmp/ados_api_50_1.pid}"
LEGACY_WEB_PID="${ADOS_WEB_PID_LEGACY:-/tmp/ados_web_50_1.pid}"
MID_API_PID="/tmp/ados_api_50_3.pid"
MID_WEB_PID="/tmp/ados_web_50_3.pid"

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

echo "== ADOS FX stack stop (50.3) =="

for f in "$API_PID_FILE" "$WEB_PID_FILE" "$LEGACY_API_PID" "$LEGACY_WEB_PID" "$MID_API_PID" "$MID_WEB_PID"; do
  if [[ -f "$f" ]]; then
    pid="$(cat "$f" 2>/dev/null || true)"
    echo "Stopping PID file $f → ${pid:-empty}"
    kill_tree "${pid:-}"
    rm -f "$f"
  fi
done

for port in 8080 5180; do
  while read -r pid; do
    [[ -z "$pid" ]] && continue
    cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    case "$cmd" in
      *run_api_local.py*|*vite*|*npm\ run\ dev*|*/src/web*)
        echo "Stopping :$port listener PID $pid ($cmd)"
        kill_tree "$pid"
        ;;
      *)
        if [[ -n "$cmd" ]]; then
          echo "Leaving :$port PID $pid (not recognized as stack): $cmd"
        fi
        ;;
    esac
  done < <(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
done

sleep 1
echo -n "8080: "; lsof -nP -iTCP:8080 -sTCP:LISTEN >/dev/null 2>&1 && echo still-up || echo free
echo -n "5180: "; lsof -nP -iTCP:5180 -sTCP:LISTEN >/dev/null 2>&1 && echo still-up || echo free
echo "Stopped (project stack only)."
