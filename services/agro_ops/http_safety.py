"""HTTP safety for official AGRO provider fetches (1.4).

Timeouts, redirect cap, size limit, 429/5xx retry, SSRF guard.
No browser-search scraping. Official URLs only.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

MAX_BYTES = 400_000
MAX_REDIRECTS = 4
TIMEOUT_SEC = 18
RETRY_STATUSES = {429, 500, 502, 503, 504}
USER_AGENT = "ADOS-AgroOps/1.6 (+https://ados.local; official-open-data probe)"

_BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",
}


def url_is_safe(url: str) -> tuple[bool, str]:
    parsed = urlparse(url or "")
    if parsed.scheme not in {"http", "https"}:
        return False, "scheme"
    host = (parsed.hostname or "").lower()
    if not host or host in _BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        return False, "host"
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except OSError:
        return False, "resolve"
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False, "private_ip"
    return True, ""


async def fetch_official(
    url: str,
    headers: dict[str, str] | None = None,
    *,
    timeout_sec: float | None = None,
    retries: int | None = None,
):
    from services.agro_ops.providers import SimpleFetchResult

    safe, reason = url_is_safe(url)
    if not safe:
        return SimpleFetchResult(error=f"ssrf_blocked:{reason}", unavailable=True, blocked=reason == "private_ip")

    import aiohttp

    hdrs = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/csv,application/xml,text/html,*/*",
    }
    if headers:
        hdrs.update(headers)

    last: SimpleFetchResult | None = None
    attempts = max(1, int(retries) + 1) if retries is not None else 3
    total_timeout = float(timeout_sec or TIMEOUT_SEC)
    for attempt in range(attempts):
        try:
            timeout = aiohttp.ClientTimeout(total=total_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url,
                    headers=hdrs,
                    allow_redirects=True,
                    max_redirects=MAX_REDIRECTS,
                    ssl=False,
                ) as resp:
                    text = await resp.text(errors="replace")
                    truncated = len(text) > MAX_BYTES
                    if truncated:
                        text = text[:MAX_BYTES]
                    ctype = str(resp.headers.get("Content-Type") or "")
                    result = SimpleFetchResult(
                        status=int(resp.status),
                        text=text,
                        headers={k: v for k, v in resp.headers.items()},
                        blocked=resp.status in {401, 403},
                        unavailable=resp.status >= 500,
                        rate_limited=resp.status == 429,
                        content_type=ctype,
                        truncated=truncated,
                    )
                    if resp.status in RETRY_STATUSES and attempt < attempts - 1:
                        retry_after = resp.headers.get("Retry-After") or "0"
                        try:
                            wait = min(4.0, float(retry_after)) if retry_after.replace(".", "", 1).isdigit() else 0.6 * (attempt + 1)
                        except Exception:
                            wait = 0.6 * (attempt + 1)
                        last = result
                        await asyncio.sleep(wait)
                        continue
                    return result
        except TimeoutError as exc:
            last = SimpleFetchResult(error=f"timeout: {exc}"[:400], unavailable=True, timed_out=True)
            if attempt < attempts - 1:
                await asyncio.sleep(0.4 * (attempt + 1))
                continue
            return last
        except Exception as exc:
            name = type(exc).__name__
            timed_out = "timeout" in name.lower() or "timeout" in str(exc).lower()
            last = SimpleFetchResult(error=str(exc)[:400], unavailable=True, timed_out=timed_out)
            if attempt < attempts - 1 and not timed_out:
                await asyncio.sleep(0.4 * (attempt + 1))
                continue
            return last
    return last or SimpleFetchResult(unavailable=True, error="fetch_failed")
