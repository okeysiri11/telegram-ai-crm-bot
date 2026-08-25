#!/usr/bin/env python3
"""Sprint 13 / 13.1 — PREVIEW public host (Cloudflare Quick Tunnel). NOT production.

Durable production is docker-compose.prod.yml on a persistent host with DNS/TLS.
This script remains as a developer/preview helper. It must never be reported as
the production URL.

The previous public deployment was two Cloudflare quick tunnels from a laptop
(one to a Vite *dev* server on :5180, one to the API on :8080 — see
docs/SPRINT_AUTO_1_8_5_REMOTE_ACCESS_RESULT.md). When the laptop or tunnel
process stopped, the public hostname went NXDOMAIN and the "production host"
died. This script is the hardened *preview* replacement:

1. requires the production SPA build (src/web/dist) — fails clearly if absent;
2. ensures the ADOS API is running on 127.0.0.1:$API_PORT (reuses a running
   API, otherwise starts API-only mode — never a second Telegram bot);
3. serves SPA + API same-origin through scripts/serve_web_gateway.py
   (production dist, no Vite dev server, no CORS split-origin);
4. exposes ONE public HTTPS tunnel (cloudflared) to the gateway;
5. refuses to report a URL until public root/assets/SPA-route/liveness/
   readiness/CRM-read/auth-gate checks all pass;
6. writes the verified URL to data/public_host.url and keeps running.

No demo/mock production fallback is introduced: the tunnel fronts the same
API process with all auth gates enforced, and every failed check exits
non-zero instead of silently reporting a broken host.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import start_remote_https as rh  # noqa: E402 — reuse tunnel/API helpers

URL_FILE = ROOT / "data" / "public_host.url"
GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = int(os.environ.get("PUBLIC_HOST_GATEWAY_PORT") or 8180)
ASSET_RE = re.compile(r"/assets/[A-Za-z0-9._-]+\.(?:js|css)")


def log(msg: str) -> None:
    print(f"[public-host] {msg}", flush=True)


def ensure_frontend_build() -> Path:
    from api.web_static import web_dist_dir

    dist = web_dist_dir()
    index = dist / "index.html"
    if not index.is_file():
        raise SystemExit(
            f"FATAL: production frontend build missing: {index}\n"
            "Run: npm install --prefix src/web && npm run build --prefix src/web"
        )
    log(f"production SPA build present: {dist}")
    return dist


def start_gateway(dist: Path) -> None:
    gateway_url = f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/"
    if rh.port_open(GATEWAY_HOST, GATEWAY_PORT) and rh.http_ok(gateway_url):
        log(f"reusing existing gateway on :{GATEWAY_PORT}")
        return
    env = os.environ.copy()
    proc = subprocess.Popen(
        [
            rh.PYTHON,
            str(ROOT / "scripts" / "serve_web_gateway.py"),
            "--host",
            GATEWAY_HOST,
            "--port",
            str(GATEWAY_PORT),
            "--proxy",
            f"http://{rh.API_HOST}:{rh.API_PORT}",
            "--dist",
            str(dist),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    rh.CHILDREN.append(proc)
    for _ in range(40):
        if proc.poll() is not None:
            out = proc.stdout.read().decode("utf-8", "replace") if proc.stdout else ""
            raise SystemExit(f"FATAL: web gateway failed to start:\n{out[-4000:]}")
        if rh.http_ok(gateway_url):
            log(f"same-origin gateway up on http://{GATEWAY_HOST}:{GATEWAY_PORT}")
            return
        time.sleep(0.5)
    raise SystemExit("FATAL: web gateway did not become healthy")


def _check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    log(f"public {name} → {'PASS' if ok else 'FAIL'} {detail}")
    if not ok:
        failures.append(name)


def resolve_via_public_dns(host: str) -> str | None:
    """Resolve an A record through public resolvers (1.1.1.1 / 8.8.8.8).

    Hosting/CI environments often run restricted internal resolvers that lag
    or refuse fresh wildcard names; the public edge is the source of truth
    for whether the tunnel hostname is actually registered.
    """
    address_re = re.compile(r"Address:\s+(\d{1,3}(?:\.\d{1,3}){3})\s*$")
    for resolver in ("1.1.1.1", "8.8.8.8"):
        try:
            out = subprocess.run(
                ["nslookup", "-type=A", host, resolver],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            continue
        for line in (out.stdout or "").splitlines():
            match = address_re.search(line.strip())
            if match and not match.group(1).startswith("127."):
                return match.group(1)
    return None


def _curl(url: str, *, pin: tuple[str, str] | None, timeout: float = 20.0) -> tuple[int, str, str]:
    """Plain curl like rh.curl_public, optionally pinned to a public edge IP."""
    if pin is None:
        return rh.curl_public(url, timeout=timeout)
    host, ip = pin
    cmd = [
        "curl", "-sS", "-L", "--max-time", str(int(timeout)),
        "--resolve", f"{host}:443:{ip}",
        "-o", "-", "-w", "\n__HTTP_CODE__:%{http_code}",
        url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    except Exception as exc:
        return 0, "", f"{type(exc).__name__}: {exc}"
    raw = proc.stdout or ""
    err = (proc.stderr or "").strip()
    if "__HTTP_CODE__:" not in raw:
        return 0, raw[:400], err or "curl produced no status"
    body, code_line = raw.rsplit("__HTTP_CODE__:", 1)
    code = int(code_line.strip()) if code_line.strip().isdigit() else 0
    return code, body, err


def verify_public(url: str) -> None:
    host = url.split("/")[2]
    deadline = time.time() + 120
    last_failures = ["not_run"]
    while time.time() < deadline:
        failures: list[str] = []
        pin: tuple[str, str] | None = None
        ok, dns_detail = rh.dns_resolves(host)
        if ok:
            log(f"public dns (system resolver) → PASS {dns_detail}")
        else:
            edge_ip = resolve_via_public_dns(host)
            if edge_ip:
                pin = (host, edge_ip)
                log(
                    f"public dns → system resolver pending ({dns_detail[:120]}); "
                    f"public DNS resolves {host} → {edge_ip}, pinning HTTP checks to the edge"
                )
            else:
                _check("dns", False, dns_detail, failures)
                last_failures = failures
                time.sleep(3)
                continue

        status, body, err = _curl(f"{url}/", pin=pin)
        root_ok = status == 200 and 'id="root"' in body
        _check("root", root_ok, f"HTTP {status}", failures)

        asset_ok = False
        asset_detail = "no asset reference found in index.html"
        match = ASSET_RE.search(body or "")
        if match:
            asset_status, _, _ = _curl(f"{url}{match.group(0)}", pin=pin)
            asset_ok = asset_status == 200
            asset_detail = f"{match.group(0)} HTTP {asset_status}"
        _check("assets", asset_ok, asset_detail, failures)

        status, body, err = _curl(f"{url}/login", pin=pin)
        _check("spa_route", status == 200 and 'id="root"' in body, f"HTTP {status}", failures)

        status, body, err = _curl(f"{url}/liveness", pin=pin)
        _check("liveness", status == 200 and '"alive"' in body, f"HTTP {status}", failures)

        status, body, err = _curl(f"{url}/readiness", pin=pin)
        ready_detail = f"HTTP {status}"
        if status == 200:
            try:
                ready_detail += f" ready={json.loads(body).get('ready')}"
            except (ValueError, TypeError):
                pass
        _check("readiness", status == 200, ready_detail, failures)

        status, body, err = _curl(f"{url}/api/auto/v1/crm/metrics", pin=pin)
        _check("crm_read", status == 200, f"HTTP {status}", failures)

        status, body, err = _curl(f"{url}/api/auto/v1/crm/manager/operational-summary", pin=pin)
        _check("auth_gate", status == 401, f"HTTP {status} (401 expected without Bearer)", failures)

        if not failures:
            return
        last_failures = failures
        time.sleep(3)
    raise SystemExit("FATAL: public host verification failed: " + ", ".join(last_failures))


def main() -> None:
    os.chdir(ROOT)
    signal.signal(signal.SIGINT, rh.cleanup)
    signal.signal(signal.SIGTERM, rh.cleanup)
    URL_FILE.parent.mkdir(parents=True, exist_ok=True)

    dist = ensure_frontend_build()
    rh.ensure_api()
    start_gateway(dist)
    binary = rh.find_cloudflared()
    public_url = rh.start_tunnel(binary, f"http://{GATEWAY_HOST}:{GATEWAY_PORT}", "public-host")
    verify_public(public_url)
    URL_FILE.write_text(public_url + "\n", encoding="utf-8")

    print()
    print("=" * 64)
    print("PREVIEW HOST VERIFIED — NOT PRODUCTION")
    print(f"Preview URL:   {public_url}")
    print(f"Liveness:      {public_url}/liveness")
    print(f"Readiness:     {public_url}/readiness")
    print(f"CRM (read):    {public_url}/api/auto/v1/crm/metrics")
    print("Cloudflare Quick Tunnels are ephemeral preview only.")
    print("Durable production: docker-compose.prod.yml + scripts/deploy_production.sh")
    print("Stop: scripts/stop_remote_https.sh (or Ctrl+C)")
    print("=" * 64)
    print()
    while True:
        time.sleep(3600)


def _terminate_children() -> None:
    for proc in reversed(rh.CHILDREN):
        if proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        rh.cleanup()
    except SystemExit as exc:
        if exc.code not in (0, None):
            _terminate_children()
        raise
