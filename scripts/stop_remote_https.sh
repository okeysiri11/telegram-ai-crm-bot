#!/usr/bin/env bash
# Stop AUTO 1.8.5 Cloudflare tunnels only.
# Does not kill local frontend (:5180), API (:8080), Telegram, or the database.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/data/auto_remote_https.pids"

stop_pid() {
  local pid="$1"
  if [[ -z "$pid" ]]; then
    return 0
  fi
  if kill -0 "$pid" 2>/dev/null; then
    echo "[stop-remote] stopping pid $pid"
    kill "$pid" 2>/dev/null || true
    sleep 0.4
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
}

if [[ -f "$PID_FILE" ]]; then
  while read -r pid; do
    stop_pid "$pid"
  done < "$PID_FILE"
  rm -f "$PID_FILE"
fi

# Only Cloudflare quick tunnels from AUTO 1.8.5 — never postgres, vite, or the bot.
for pattern in \
  "cloudflared tunnel --url http://127.0.0.1:4173" \
  "cloudflared tunnel --url http://127.0.0.1:5180" \
  "cloudflared tunnel --url http://127.0.0.1:8080"
do
  for pid in $(pgrep -f "$pattern" || true); do
    stop_pid "$pid"
  done
done

echo "[stop-remote] tunnel processes stopped. Local http://127.0.0.1:5180 and :8080 are unchanged."
echo "To stop local frontend: kill the Vite process on :5180"
echo "To stop API+Telegram: stop the single main.py / startup.py process on :8080"
