#!/usr/bin/env bash
# Recruiting Redis (Docker Compose) — start | stop | health | logs
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="$ROOT/docker-compose.recruiting.yml"
NAME="recruiting-redis"

compose() {
  docker_bin=""
  if command -v docker >/dev/null 2>&1; then
    docker_bin="$(command -v docker)"
  elif [[ -x /usr/local/bin/docker ]]; then
    docker_bin="/usr/local/bin/docker"
  fi
  if [[ -z "$docker_bin" ]] || ! "$docker_bin" info >/dev/null 2>&1; then
    echo "BLOCKED: Docker is not available."
    echo "Docker CLI is missing or the Docker.app volume is not mounted (expected /usr/local/bin/docker)."
    echo "Start Docker Desktop or mount the volume, then retry. Do not install Redis with Homebrew."
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
