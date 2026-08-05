"""Prompt firewall for AI Provider Hub — Sprint 30.9 Beta Hardening.

Extends APH invoke/assemble_prompt. Not a parallel AI security product.
Mirrors client heuristics in src/web/src/ai-runtime/aiPromptSecurity.ts.
"""

from __future__ import annotations

import re
import time
from typing import Any

_UNSAFE = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|system)\s+", re.I),
    re.compile(r"you\s+are\s+now\s+(dan|jailbroken|unrestricted)", re.I),
    re.compile(r"system\s*prompt\s*:", re.I),
    re.compile(r"reveal\s+(your\s+)?(system|hidden)\s+prompt", re.I),
    re.compile(r"bypass\s+(safety|security|filter|guardrail)", re.I),
    re.compile(r"<\s*script\b", re.I),
    re.compile(r"\bunion\s+select\b", re.I),
    re.compile(r"\b(drop|truncate)\s+table\b", re.I),
]

# Simple in-process rate window (per process) — complements HTTP rate_limit_middleware
_BURST: dict[str, list[float]] = {}
_BURST_WINDOW = 60.0
_BURST_MAX = 40


def estimate_tokens(text: str) -> int:
    return max(1, (len(text.strip()) + 3) // 4)


def sanitize_prompt(text: str) -> str:
    out = text.replace("\x00", "")
    out = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", out)
    out = re.sub(r"(?is)<\s*script[^>]*>.*?<\s*/\s*script\s*>", "[removed]", out)
    return out.strip()


def detect_unsafe(text: str) -> list[str]:
    reasons: list[str] = []
    for pat in _UNSAFE:
        if pat.search(text):
            reasons.append(f"pattern:{pat.pattern[:48]}")
    if len(text) > 32000:
        reasons.append("length_extreme")
    return reasons


def check_abuse(actor: str = "hub") -> tuple[bool, int]:
    now = time.time()
    bucket = [t for t in _BURST.get(actor, []) if now - t < _BURST_WINDOW]
    bucket.append(now)
    _BURST[actor] = bucket
    return len(bucket) > _BURST_MAX, len(bucket)


def reset_abuse_state() -> None:
    """Clear in-process abuse windows (tests / process recycle). Sprint 37.5."""
    _BURST.clear()


def guard_prompt(
    raw: str,
    *,
    max_tokens: int = 4096,
    actor: str = "hub",
) -> dict[str, Any]:
    sanitized = sanitize_prompt(raw or "")
    reasons: list[str] = []
    if not sanitized:
        return {
            "ok": False,
            "risk": "blocked",
            "sanitized": "",
            "reasons": ["empty"],
            "token_estimate": 0,
            "truncated": False,
        }

    unsafe = detect_unsafe(sanitized)
    reasons.extend(unsafe)
    abused, count = check_abuse(actor)
    if abused:
        reasons.append(f"abuse_rate:{count}")

    truncated = False
    tokens = estimate_tokens(sanitized)
    if tokens > max_tokens:
        sanitized = sanitized[: max_tokens * 4]
        truncated = True
        tokens = estimate_tokens(sanitized)
        reasons.append("token_truncated")

    blocked = bool(unsafe) or abused
    return {
        "ok": not blocked,
        "risk": "blocked" if blocked else ("suspicious" if reasons else "safe"),
        "sanitized": sanitized,
        "reasons": reasons,
        "token_estimate": tokens,
        "truncated": truncated,
    }
