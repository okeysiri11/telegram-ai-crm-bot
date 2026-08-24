#!/usr/bin/env python3
"""AUTO 1.8.5 — temporary HTTPS tunnels for the CURRENT local ADOS app.

Frontend tunnel: Vite on 127.0.0.1:5180 (relative /api proxied to :8080).
Backend tunnel: API on 127.0.0.1:8080 (public health URL).

Reuses the running API on :8080 when present (does not start a second bot).
Does not report a URL until system DNS + HTTPS checks pass without --resolve.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL_FILE = ROOT / "data" / "auto_remote_https.url"
PID_FILE = ROOT / "data" / "auto_remote_https.pids"
API_HOST = "127.0.0.1"
API_PORT = int(os.environ.get("API_PORT") or 8080)
FRONTEND_PORT = int(os.environ.get("VITE_PORT") or os.environ.get("PORT") or 5180)
PY = ROOT / ".venv" / "bin" / "python"
PYTHON = str(PY) if PY.is_file() else sys.executable
CHILDREN: list[subprocess.Popen] = []
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def log(msg: str) -> None:
    print(f"[remote-https] {msg}", flush=True)


def port_open(host: str, port: int) -> bool:
    sock = socket.socket()
    sock.settimeout(0.4)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def http_ok(url: str, timeout: float = 2.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as res:
            return 200 <= int(res.status) < 500
    except Exception:
        return False


def _write_pids() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    pids = [str(proc.pid) for proc in CHILDREN if proc.poll() is None]
    PID_FILE.write_text("\n".join(pids) + ("\n" if pids else ""), encoding="utf-8")


def dns_resolves(host: str) -> tuple[bool, str]:
    """System resolver only — same path a phone on this LAN uses. No 8.8.8.8 bypass."""
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        ns = subprocess.run(
            ["nslookup", host],
            capture_output=True,
            text=True,
            timeout=10,
        )
        detail = (ns.stdout or "") + (ns.stderr or "")
        return False, f"gaierror={exc}; nslookup={detail.strip()[:400]}"
    ips = sorted({item[4][0] for item in infos})
    return True, ",".join(ips)


def curl_public(url: str, timeout: float = 20.0) -> tuple[int, str, str]:
    """Plain curl — no --resolve, no custom DNS."""
    cmd = [
        "curl",
        "-sS",
        "-L",
        "--max-time",
        str(int(timeout)),
        "-D",
        "-",
        "-o",
        "-",
        "-w",
        "\n__HTTP_CODE__:%{http_code}",
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
    if proc.returncode != 0 and code == 0:
        return 0, body[:400], err or f"curl_exit={proc.returncode}"
    return code, body, err


def _tunnel_error(body: str) -> str | None:
    lower = body.lower()
    if "error 1033" in lower or "cloudflare error 1033" in lower:
        return "1033"
    if "502 bad gateway" in lower or "error 502" in lower:
        return "502"
    if "this tunnel is either not running" in lower:
        return "tunnel_not_running"
    if "could not resolve host" in lower:
        return "dns"
    return None


def verify_frontend(url: str) -> None:
    host = url.split("/")[2]
    last_fail = "not_run"
    deadline = time.time() + 90
    while time.time() < deadline:
        failed: list[str] = []
        ok, dns_detail = dns_resolves(host)
        log(f"frontend DNS {host} → {'PASS ' + dns_detail if ok else 'FAIL ' + dns_detail}")
        if not ok:
            failed.append("dns")
            last_fail = ", ".join(failed)
            time.sleep(3)
            continue
        for name, path in (
            ("frontend", "/"),
            ("login", "/login"),
            ("auto_workspace", "/workspace/auto"),
        ):
            status, body, err = curl_public(f"{url}{path}")
            snippet = (body or err).replace("\n", " ")[:180]
            log(f"public {name} {url}{path} → {status} {snippet}")
            tunnel_err = _tunnel_error(body + "\n" + err)
            if tunnel_err:
                failed.append(f"{name}_{tunnel_err}")
                continue
            if status not in {200, 301, 302, 303, 307, 308}:
                failed.append(f"{name}={status}")
                continue
            if name == "frontend" and "Enterprise Web Platform" not in body and 'id="root"' not in body:
                failed.append("frontend_html")
            if name == "login" and "Enterprise Web Platform" not in body and 'id="root"' not in body:
                failed.append("login_html")
        if not failed:
            return
        last_fail = ", ".join(failed)
        time.sleep(3)
    raise SystemExit("public frontend HTTPS checks failed: " + last_fail)


def verify_backend(url: str) -> None:
    host = url.split("/")[2]
    last_fail = "not_run"
    deadline = time.time() + 90
    while time.time() < deadline:
        failed: list[str] = []
        ok, dns_detail = dns_resolves(host)
        log(f"backend DNS {host} → {'PASS ' + dns_detail if ok else 'FAIL ' + dns_detail}")
        if not ok:
            failed.append("dns")
            last_fail = ", ".join(failed)
            time.sleep(3)
            continue
        status, body, err = curl_public(f"{url}/api/auto-ops/v1/health")
        snippet = (body or err).replace("\n", " ")[:180]
        log(f"public backend health → {status} {snippet}")
        tunnel_err = _tunnel_error(body + "\n" + err)
        if tunnel_err:
            failed.append(tunnel_err)
        elif status != 200:
            failed.append(f"health={status}")
        elif "AUTO_1.8.5" not in body:
            failed.append("health_payload")
        if not failed:
            return
        last_fail = ", ".join(failed)
        time.sleep(3)
    raise SystemExit("public backend HTTPS checks failed: " + last_fail)


def cleanup(_signum=None, _frame=None) -> None:
    for proc in reversed(CHILDREN):
        if proc.poll() is None:
            proc.terminate()
    deadline = time.time() + 5
    for proc in CHILDREN:
        if proc.poll() is None:
            try:
                proc.wait(timeout=max(0.1, deadline - time.time()))
            except subprocess.TimeoutExpired:
                proc.kill()
    if PID_FILE.is_file():
        PID_FILE.unlink(missing_ok=True)
    raise SystemExit(0)


def find_cloudflared() -> str:
    found = shutil.which("cloudflared")
    if found:
        return found
    local = ROOT / "scripts" / ".bin" / "cloudflared"
    if local.is_file() and os.access(local, os.X_OK):
        return str(local)
    raise SystemExit(
        "cloudflared is not installed. Install it (brew install cloudflared) and re-run scripts/start_remote_https.sh"
    )


def ensure_api() -> None:
    health = f"http://{API_HOST}:{API_PORT}/health"
    if port_open(API_HOST, API_PORT) and http_ok(health):
        log(f"reusing existing API at {health} (no second Telegram bot)")
        return
    log("starting local API only (scripts/run_api_local.py) — Telegram polling is not started")
    env = os.environ.copy()
    env.setdefault("ENVIRONMENT", "development")
    env.setdefault("REDIS_REQUIRED", "false")
    env.setdefault("API_HOST", API_HOST)
    env.setdefault("API_PORT", str(API_PORT))
    proc = subprocess.Popen(
        [PYTHON, str(ROOT / "scripts" / "run_api_local.py")],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    CHILDREN.append(proc)
    for _ in range(60):
        if proc.poll() is not None:
            out = proc.stdout.read().decode("utf-8", "replace") if proc.stdout else ""
            raise SystemExit(f"API failed to start:\n{out[-4000:]}")
        if http_ok(health):
            log("API is up")
            return
        time.sleep(0.5)
    raise SystemExit("API did not become healthy on /health")


def ensure_frontend() -> None:
    if port_open("127.0.0.1", FRONTEND_PORT) and http_ok(f"http://127.0.0.1:{FRONTEND_PORT}/"):
        log(f"reusing existing Vite frontend on :{FRONTEND_PORT}")
        return
    raise SystemExit(
        f"Vite is not listening on 127.0.0.1:{FRONTEND_PORT}. "
        "Start it with: npm run dev -- --host 0.0.0.0 --port 5180"
    )


def start_tunnel(bin_path: str, local_url: str, label: str) -> str:
    log(f"starting Cloudflare quick tunnel ({label}) → {local_url}")
    proc = subprocess.Popen(
        [bin_path, "tunnel", "--url", local_url, "--no-autoupdate"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    CHILDREN.append(proc)
    _write_pids()
    assert proc.stdout is not None
    deadline = time.time() + 45
    collected: list[str] = []
    while time.time() < deadline:
        if proc.poll() is not None:
            rest = proc.stdout.read() or ""
            raise SystemExit(f"cloudflared ({label}) exited:\n{''.join(collected) + rest}")
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        collected.append(line)
        match = URL_RE.search(line)
        if match:
            url = match.group(0)
            log(f"{label} candidate URL captured (not reported until verified): {url}")
            return url
    raise SystemExit(f"cloudflared ({label}) did not print a trycloudflare.com URL")


def main() -> None:
    os.chdir(ROOT)
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    URL_FILE.parent.mkdir(parents=True, exist_ok=True)
    ensure_api()
    ensure_frontend()
    binary = find_cloudflared()
    frontend_url = start_tunnel(binary, f"http://127.0.0.1:{FRONTEND_PORT}", "frontend")
    backend_url = start_tunnel(binary, f"http://{API_HOST}:{API_PORT}", "backend")
    URL_FILE.write_text(f"{frontend_url}\n{backend_url}\n", encoding="utf-8")
    _write_pids()
    verify_frontend(frontend_url)
    verify_backend(backend_url)
    print()
    print("=" * 64)
    print("AUTO 1.8.5 REMOTE ACCESS FIXED")
    print("TEMPORARY: YES")
    print("Временная ссылка работает только пока компьютер и tunnel process включены.")
    print(f"Frontend URL: {frontend_url}")
    print(f"Backend URL:  {backend_url}")
    print(f"Health URL:   {backend_url}/api/auto-ops/v1/health")
    print("Local still works: http://127.0.0.1:5180  and  http://127.0.0.1:8080")
    print("Stop tunnel: scripts/stop_remote_https.sh")
    print("=" * 64)
    print(f"ОТКРОЙ С ТЕЛЕФОНА: {frontend_url}")
    print("Leave this process running. Ctrl+C stops the tunnel (not local :5180/:8080).")
    print()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
