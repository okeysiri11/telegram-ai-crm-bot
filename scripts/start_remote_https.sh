#!/usr/bin/env bash
# Temporary HTTPS access to the CURRENT local ADOS app (AUTO 1.8.5).
# Does not start a second Telegram bot. Computer must stay on.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="python3"
fi
exec "$PY" "$ROOT/scripts/start_remote_https.py"
