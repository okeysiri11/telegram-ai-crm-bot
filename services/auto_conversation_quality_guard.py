"""Sprint 46.1 — Conversation Quality Guard (final validation before send)."""

from __future__ import annotations

import re
from typing import Any

from services.auto_client_output import sanitize_ai_reply_for_client
from services.auto_human_conversation_policy import resolve_ai_style

_ENGLISH_CLIENT = re.compile(
    r"\b(Please|Correct|Would you|Could you|Score|Priority|Dept|Intent|"
    r"Warning|Critical|Busy|Subscription|Analytics|confirm that|"
    r"Did I understand|physical or legal)\b",
    re.I,
)

_CROSS_SELL = re.compile(
    r"(аренд[ауеы]|страховк|кредит(?!н)|лизинг.*(ещ[её]|тоже)|"
    r"нужна ли аренда|физическое или юридическое)",
    re.I,
)

_CONFIRM_OBVIOUS = re.compile(
    r"правильно ли я понял|верно ли я|подтвердите[, ]+что|укажите год/пробег/комплектацию",
    re.I,
)

_MULTI_QUESTION = re.compile(r"\?")


def apply_conversation_quality_guard(
    text: str,
    *,
    known: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    role: str = "client",
    debug: bool = False,
    allow_cross_sell: bool | None = None,
) -> str:
    """
    Rewrite client-facing reply before send.
    Deterministic checks — not an LLM call.
    """
    style = resolve_ai_style(settings)
    if not style.get("human_conversation_guard", True):
        return sanitize_ai_reply_for_client(text or "", role=role, debug=debug)

    out = (text or "").strip()
    known = known or {}

    # Strip internal CRM meta always for clients
    out = sanitize_ai_reply_for_client(out, role=role, debug=debug)

    # No English client-facing sentences
    if _ENGLISH_CLIENT.search(out):
        out = _ENGLISH_CLIENT.sub("", out)
        out = re.sub(r"\n{3,}", "\n\n", out).strip()

    # No confirm-the-obvious / questionnaire dumps
    if style.get("confirm_understood") == "ambiguity_only" or style.get("confirm_understood") == "never":
        out = _CONFIRM_OBVIOUS.sub("", out)

    # Cross-sell off by default
    cross = style.get("cross_sell", False) if allow_cross_sell is None else allow_cross_sell
    if not cross:
        # Drop lines that push other products after a completed request
        lines = []
        for line in out.split("\n"):
            if _CROSS_SELL.search(line) and not re.search(r"лизинг", (known.get("intent") or ""), re.I):
                # keep leasing replies when intent is leasing
                if "лизинг" in line.lower() and (known.get("intent") or "").upper() == "LEASING":
                    lines.append(line)
                elif "лизинг" not in line.lower():
                    continue
                else:
                    continue
            else:
                lines.append(line)
        out = "\n".join(lines).strip()

    # Don't re-ask known brand/budget/city
    if known.get("brand") and re.search(r"какую\s+марку|укажите\s+марку", out, re.I):
        out = re.sub(r"[^\n]*какую\s+марку[^\n]*", "", out, flags=re.I)
    if known.get("budget_max") and re.search(r"какой\s+бюджет|укажите\s+бюджет", out, re.I):
        out = re.sub(r"[^\n]*бюджет[^\n]*\?", "", out, flags=re.I)
    if known.get("city") and re.search(r"какой\s+город|укажите\s+город", out, re.I):
        out = re.sub(r"[^\n]*город[^\n]*\?", "", out, flags=re.I)

    # At most one question unless detailed style
    if style.get("conversation_style") == "concise":
        qs = list(_MULTI_QUESTION.finditer(out))
        if len(qs) > 1:
            # keep text up to first question mark
            out = out[: qs[0].end()].strip()

    # Length: prefer 1–4 short sentences for concise
    if style.get("conversation_style") == "concise":
        # Split cards from prose: keep after blank line intact if looks like car cards
        parts = out.split("\n\n")
        prose = parts[0] if parts else out
        sentences = re.split(r"(?<=[.!?…])\s+", prose.strip())
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > 4 and "🚗" not in prose:
            prose = " ".join(sentences[:4])
            parts[0] = prose
            out = "\n\n".join(parts)

    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out or "Готово."
