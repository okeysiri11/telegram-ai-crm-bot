"""Sprint 46.1 — Localization gate: forbid unregistered English user-facing strings."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]

# Paths scanned for Auto Telegram client-facing surfaces
SCAN_GLOBS = (
    "auto_vertical_handlers.py",
    "routers/auto_*.py",
    "services/auto_*.py",
    "services/pg_commercial_billing_engine.py",
    "dealer_onboarding_handlers.py",
    "automotive_partner_handlers.py",
)

# Allowed English tokens (brands, currency codes, technical ids kept internal)
ALLOWED_ENGLISH_TOKENS = frozenset(
    {
        "VIN",
        "BMW",
        "X5",
        "X3",
        "X6",
        "X7",
        "Mercedes",
        "GLE",
        "GLC",
        "Audi",
        "Toyota",
        "USD",
        "EUR",
        "UAH",
        "USDT",
        "TRC20",
        "ERC20",
        "Instagram",
        "Facebook",
        "TikTok",
        "Telegram",
        "AI",
        "CPL",
        "ID",
        "SLA",
        "OK",
        "N/A",
    }
)

FORBIDDEN_PHRASES = (
    "Dealer rates not configured",
    "No active tenant context",
    "unlimited channels",
    "AI ecosystem access",
    "custom plan",
    "dedicated support",
    "Profit Calculator",
    "Expected profit",
    "Sale price",
    "Total cost",
    "Automotive module temporarily unavailable",
    "pending payments",
    "Score:",
    "Priority:",
    "Dept:",
    "Intent:",
    "Warning",
    "Critical",
    "Busy",
    "STARTER",
    "ENTERPRISE",
)

# English sentence-ish literals (heuristic for message.answer style strings)
_EN_SENTENCE = re.compile(
    r"\b(the|and|not|configured|update|rates|channel|please|select|error|failed|"
    r"temporarily|unavailable|subscription|support|analytics|priority|department)\b",
    re.I,
)


def _iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(REPO_ROOT.glob(pattern))
    exclude = {
        (REPO_ROOT / "services/auto_localization_gate.py").resolve(),
        (REPO_ROOT / "services/auto_client_output.py").resolve(),
        (REPO_ROOT / "services/auto_conversation_quality_guard.py").resolve(),
        (REPO_ROOT / "services/auto_human_conversation_policy.py").resolve(),
        (REPO_ROOT / "services/auto_dialog_state.py").resolve(),
    }
    return sorted({p.resolve() for p in files if p.is_file() and p.resolve() not in exclude})


def _string_literals(path: Path) -> list[tuple[int, str]]:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((getattr(node, "lineno", 0), node.value))
    return out


def _is_user_facing_candidate(s: str) -> bool:
    if len(s) < 8:
        return False
    if s.startswith(("http", "/", ".", "_", "billing:", "dealer_cfg:", "partner:", "onboard:")):
        return False
    if s.startswith(("f\"", "r\"", "SELECT ", "INSERT ", "UPDATE ", "FROM ")):
        return False
    # mostly latin letters → likely English UI
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if "a" <= c.lower() <= "z")
    return (latin / len(letters)) > 0.85 and _EN_SENTENCE.search(s) is not None


def scan_user_facing_strings(
    paths: Iterable[Path] | None = None,
    *,
    locale: str = "ru",
) -> list[dict[str, str | int]]:
    """
    Return list of violations: {file, line, text, reason}.
    For locale=ru, any forbidden phrase or unregistered English UI string fails.
    """
    if locale != "ru":
        return []
    violations: list[dict[str, str | int]] = []
    for path in paths or _iter_scan_files():
        rel = str(path.relative_to(REPO_ROOT)) if path.is_absolute() else str(path)
        for lineno, text in _string_literals(path):
            for phrase in FORBIDDEN_PHRASES:
                if phrase.lower() in text.lower():
                    # Internal plan id keys / callback fragments are allowed
                    if phrase in {"STARTER", "ENTERPRISE", "PRO", "BUSINESS", "Warning", "Critical", "Busy"}:
                        stripped = text.strip()
                        if stripped in {"STARTER", "PRO", "BUSINESS", "ENTERPRISE", "starter", "pro", "business", "enterprise"}:
                            continue
                        if "plan:" in text.lower() or "plan_code" in text.lower() or "BillingPlanCode" in text:
                            continue
                        if phrase in {"Warning", "Critical", "Busy"} and len(stripped) <= 12:
                            continue
                    violations.append(
                        {
                            "file": rel,
                            "line": lineno,
                            "text": text[:160],
                            "reason": f"forbidden_phrase:{phrase}",
                        }
                    )
                    break
            else:
                if _is_user_facing_candidate(text):
                    # allow if every english word is in allowlist (rough)
                    words = re.findall(r"[A-Za-z]{2,}", text)
                    if words and all(w in ALLOWED_ENGLISH_TOKENS or w.upper() in ALLOWED_ENGLISH_TOKENS for w in words):
                        continue
                    violations.append(
                        {
                            "file": rel,
                            "line": lineno,
                            "text": text[:160],
                            "reason": "unregistered_english_ui",
                        }
                    )
    return violations
