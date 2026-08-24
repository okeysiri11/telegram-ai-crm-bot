# Mobile public access recovery — 20 Aug 2026

Laptop processes after the drop: 1× API (`run_api_local.py` :8080), 1× Vite (:5180), **3× stale cloudflared** (two on 5180, one on 8080). Telegram polling was not running (API-only, no second bot).

Stale tunnels were stopped. A **new** frontend quick tunnel was created. Do not reuse old hostnames.

Public phone URL:

https://logos-philip-environment-determination.trycloudflare.com

Look for `LIVE • k7p2` in the mobile header. If Chrome still says «Офлайн-копия», close that tab and open this **new** URL (old hosts are 530 / NXDOMAIN).
