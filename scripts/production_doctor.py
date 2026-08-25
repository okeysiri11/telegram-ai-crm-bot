#!/usr/bin/env python3
"""Sprint 13.1 — production doctor. Offline by default. Never prints secret values."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_PASSWORDS = frozenset({"", "CHANGE_ME", "postgres", "admin", "password", "secret"})
SECRET_VALUE_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?(sk-|ghp_|xox[baprs]-|AKIA)[A-Za-z0-9_\-]{8,}"
)


def _ok(name: str, passed: bool, detail: str) -> dict[str, str | bool]:
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    return {"name": name, "ok": passed, "detail": detail}


def check_files() -> list[dict[str, str | bool]]:
    required = {
        "Dockerfile": ROOT / "Dockerfile",
        "compose": ROOT / "docker-compose.prod.yml",
        "entrypoint": ROOT / "docker-entrypoint.sh",
        "nginx": ROOT / "nginx.conf",
        "env_example": ROOT / ".env.example",
        "deploy": ROOT / "scripts" / "deploy_production.sh",
        "rollback": ROOT / "scripts" / "rollback_production.sh",
        "backup": ROOT / "scripts" / "backup_postgres.sh",
        "restore": ROOT / "scripts" / "restore_postgres.sh",
        "crm_smoke": ROOT / "scripts" / "crm_production_smoke.py",
        "preview_tunnel": ROOT / "scripts" / "start_public_host.py",
        "render_blueprint": ROOT / "render.yaml",
        "web_dockerfile": ROOT / "Dockerfile.web",
        "production_web": ROOT / "scripts" / "run_production_web.py",
    }
    results = []
    for name, path in required.items():
        results.append(_ok(f"artifact.{name}", path.is_file(), str(path.relative_to(ROOT))))
    return results


def check_dockerfile() -> list[dict[str, str | bool]]:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    return [
        _ok("dockerfile.entrypoint", "ENTRYPOINT" in text, "docker-entrypoint.sh"),
        _ok("dockerfile.healthcheck", "HEALTHCHECK" in text, "/liveness"),
        _ok("dockerfile.revision", "GIT_SHA" in text, "build-arg GIT_SHA"),
        _ok("dockerfile.nonroot", "USER ados" in text, "uid 10001"),
    ]


def check_compose() -> list[dict[str, str | bool]]:
    text = (ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    postgres_block = text.split("  redis:")[0]
    published_pg = bool(re.search(r"ports:\s*\n\s*-\s*[\"']?\d+:5432", postgres_block))
    return [
        _ok("compose.postgres_internal", not published_pg, "5432 not published"),
        _ok("compose.bot_healthcheck", "curl -sf http://127.0.0.1:8080/health" in text, "bot /health"),
        _ok("compose.not_tunnel", "NOT production" in text, "quick tunnel demoted"),
        _ok("compose.git_sha", "GIT_SHA" in text, "revision injected"),
    ]


def check_nginx() -> list[dict[str, str | bool]]:
    text = (ROOT / "nginx.conf").read_text(encoding="utf-8")
    return [
        _ok("nginx.health", "location /health" in text, "proxied"),
        _ok("nginx.liveness", "location /liveness" in text, "proxied"),
        _ok("nginx.readiness", "location /readiness" in text, "proxied"),
    ]


def check_tunnel_demoted() -> list[dict[str, str | bool]]:
    preview = (ROOT / "scripts" / "start_public_host.py").read_text(encoding="utf-8")
    deploy_doc = (ROOT / "docs" / "deployment.md").read_text(encoding="utf-8")
    return [
        _ok("tunnel.script_not_production", "NOT production" in preview, "start_public_host.py"),
        _ok("tunnel.banner_preview", "PREVIEW HOST VERIFIED" in preview, "banner"),
        _ok("tunnel.docs_preview", "PREVIEW" in deploy_doc and "not production" in deploy_doc.lower(), "deployment.md"),
    ]


def check_alembic() -> list[dict[str, str | bool]]:
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        heads = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini"))).get_heads()
        return [_ok("alembic.single_head", len(heads) == 1, ",".join(heads))]
    except Exception as exc:
        return [_ok("alembic.single_head", False, str(exc))]


def check_secrets_tracked() -> list[dict[str, str | bool]]:
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    forbidden = {".env", ".env.local", ".env.production"}
    leaked = sorted(forbidden.intersection(tracked))
    hits: list[str] = []
    for rel in tracked:
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size > 2_000_000 or rel == ".env.example":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if SECRET_VALUE_RE.search(text):
            hits.append(rel)
    return [
        _ok("secrets.untracked_env", not leaked, "none" if not leaked else ",".join(leaked)),
        _ok("secrets.no_live_tokens", not hits, "none" if not hits else ",".join(hits[:8])),
    ]


def check_production_env_file(*, production: bool) -> list[dict[str, str | bool]]:
    path = ROOT / ".env.production"
    if not production:
        return [_ok("env.production_file", True, "skipped (offline engineering mode)")]
    if not path.is_file():
        return [_ok("env.production_file", False, ".env.production missing")]
    text = path.read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        values[key.strip()] = raw.strip().strip("'\"")
    weak = [
        key
        for key in ("POSTGRES_PASSWORD", "GRAFANA_ADMIN_PASSWORD", "IAM_JWT_SECRET")
        if values.get(key, "CHANGE_ME") in PLACEHOLDER_PASSWORDS
    ]
    return [_ok("env.production_placeholders", not weak, "set" if not weak else f"placeholder:{','.join(weak)}")]


def check_compose_binary() -> list[dict[str, str | bool]]:
    docker = subprocess.run(["which", "docker"], capture_output=True, text=True)
    if docker.returncode != 0:
        return [_ok("compose.binary", True, "docker unavailable — structural checks only")]
    env_file = ROOT / ".env.production"
    created = False
    if not env_file.is_file():
        env_file.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
        created = True
    try:
        proc = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.prod.yml", "config"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return [_ok("compose.config", proc.returncode == 0, "ok" if proc.returncode == 0 else (proc.stderr or proc.stdout)[-400:])]
    finally:
        if created:
            env_file.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", default=True, help="Engineering checks only (default).")
    parser.add_argument("--production", action="store_true", help="Also require a real .env.production without placeholders.")
    args = parser.parse_args()
    checks: list[dict[str, str | bool]] = []
    checks.extend(check_files())
    checks.extend(check_dockerfile())
    checks.extend(check_compose())
    checks.extend(check_nginx())
    checks.extend(check_tunnel_demoted())
    checks.extend(check_alembic())
    checks.extend(check_secrets_tracked())
    checks.extend(check_production_env_file(production=args.production))
    checks.extend(check_compose_binary())
    failed = [item for item in checks if not item["ok"]]
    print(f"PRODUCTION_DOCTOR={'FAIL' if failed else 'PASS'} failed={len(failed)} total={len(checks)}")
    return 1 if failed else 0


if __name__ == "__main__":
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    raise SystemExit(main())
