#!/usr/bin/env bash
# Local development — existing API + existing Enterprise Web. No second bot.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="python3"
fi

echo "ADOS local development"
echo "  Backend:  $PY scripts/run_api_local.py   → http://127.0.0.1:8080"
echo "  Frontend: npm run dev --prefix src/web -- --host 127.0.0.1 --port 5180"
echo "  Combined: npm run dev:all"
echo
echo "Does not start Telegram polling. Keep a single bot instance (startup.py / main.py) if you need Telegram."

exec npm run dev:all
