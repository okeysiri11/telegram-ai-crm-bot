#!/usr/bin/env bash
# Recruiting Redis (Docker Compose) — start | stop | health | logs
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="$ROOT/docker-compose.recruiting.yml"
NAME="recruiting-redis"

compose() {
  candidates=()
  if [[ -x "${HOME}/.local/bin/docker" ]]; then
    candidates+=("${HOME}/.local/bin/docker")
  fi
  if command -v docker >/dev/null 2>&1; then
    candidates+=("$(command -v docker)")
  fi
  if [[ -x /usr/local/bin/docker ]]; then
    candidates+=("/usr/local/bin/docker")
  fi
  docker_bin=""
  for cand in "${candidates[@]}"; do
    if "$cand" info >/dev/null 2>&1; then
      docker_bin="$cand"
      break
    fi
  done
  if [[ -z "$docker_bin" ]]; then
    echo "BLOCKED: Docker daemon is not available."
    echo "/usr/local/bin/docker is a dangling symlink to /Volumes/Docker 1/Docker.app (volume not mounted)."
    echo "A valid Docker.app exists at ~/Desktop/Docker.app — start it, then: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "Do not install Redis with Homebrew."
    return 127
  fi
  "$docker_bin" compose -f "$FILE" "$@"
}

cmd="${1:-health}"
case "$cmd" in
  start)
    compose up -d
    compose ps
    compose exec -T redis redis-cli ping
    ;;
  stop)
    compose down
    ;;
  health)
    compose ps
    compose exec -T redis redis-cli ping
    ;;
  logs)
    compose logs -f redis
    ;;
  *)
    echo "Usage: $0 start|stop|health|logs"
    exit 2
    ;;
esac
