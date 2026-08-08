#!/usr/bin/env python3
"""Live Telegram bot infrastructure check — Sprint 39.1.

Validates token presence, getMe, webhook mode, and recent compose logs for polling.
Does not send spam messages to users; optional OWNER_ID probe via getChat if set.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


async def _telegram_checks() -> list[str]:
    failures: list[str] = []
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        return ["BOT_TOKEN missing in environment / .env"]

    try:
        from aiogram import Bot
    except ImportError:
        return ["aiogram not installed in this Python env"]

    bot = Bot(token=token)
    try:
        me = await bot.get_me()
        print(f"[PASS] getMe @{me.username} id={me.id}")
        wh = await bot.get_webhook_info()
        url = (wh.url or "").strip()
        if url:
            print(f"[PASS] webhook mode url={url}")
        else:
            print("[PASS] webhook empty → polling mode expected")
        owner = os.environ.get("OWNER_ID", "").strip()
        if owner.isdigit():
            try:
                chat = await bot.get_chat(int(owner))
                print(f"[PASS] getChat OWNER_ID={owner} type={chat.type}")
            except Exception as exc:  # noqa: BLE001
                # Not fatal for infra — owner may have never started the bot
                print(f"[WARN] getChat OWNER_ID failed: {type(exc).__name__}: {exc}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"Telegram API failed: {type(exc).__name__}: {exc}")
    finally:
        await bot.session.close()
    return failures


def _log_checks() -> list[str]:
    failures: list[str] = []
    proc = subprocess.run(
        ["docker", "compose", "logs", "bot", "--tail", "400"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    text = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        failures.append("docker compose logs bot failed")
        return failures
    if re.search(r"Start polling|Run polling for bot", text):
        print("[PASS] logs show polling started")
    else:
        # Container may have been up long enough that startup lines rotated out
        print("[WARN] polling start line not in last 400 log lines (may have rotated)")
    if re.search(r"TelegramNetworkError|ClientConnectorError.*telegram", text):
        print("[WARN] transient Telegram network errors present in logs (reconnect class)")
    else:
        print("[PASS] no recent TelegramNetworkError in tail")
    return failures


def main() -> int:
    _load_dotenv()
    print("=== Telegram bot validation (Sprint 39.1) ===")
    failures = asyncio.run(_telegram_checks())
    failures.extend(_log_checks())
    if failures:
        for item in failures:
            print(f"[FAIL] {item}")
        print("TELEGRAM_GATE=FAIL")
        return 1
    print("TELEGRAM_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
