"""HOTFIX 46.2.1 — Add-vehicle VIN decision (deterministic, shared by text + buttons)."""

from __future__ import annotations

from typing import Literal

VinDecision = Literal["yes", "no", "unknown"]

VIN_YES_NORMALIZED = frozenset(
    {
        "да",
        "yes",
        "1",
        "+",
        "✅",
        "✅ да",
        "добавить",
        "добавить vin",
        "vin",
    }
)

VIN_NO_NORMALIZED = frozenset(
    {
        "нет",
        "no",
        "2",
        "-",
        "пропустить",
        "skip",
        "без vin",
        "без вин",
        "❌",
        "❌ нет",
        "не надо",
        "не нужно",
    }
)


def normalize_vin_decision_input(text: str | None) -> str:
    raw = (text or "").strip()
    # strip zero-width / weird spaces
    raw = raw.replace("\u200b", "").replace("\xa0", " ")
    return " ".join(raw.lower().split())


def resolve_vin_decision(text: str | None = None, *, callback_data: str | None = None) -> VinDecision:
    """Single resolver for button callbacks and free-text Да/Нет/1/2."""
    if callback_data:
        cd = callback_data.strip().lower()
        if cd in {
            "auto:add:vin:yes",
            "addcar:vin:yes",
            "vin_yes",
            "ac:vin:add",
        }:
            return "yes"
        if cd in {
            "auto:add:vin:no",
            "addcar:vin:no",
            "vin_no",
            "ac:vin:skip",
        }:
            return "no"

    norm = normalize_vin_decision_input(text)
    if not norm:
        return "unknown"
    if norm in VIN_YES_NORMALIZED:
        return "yes"
    if norm in VIN_NO_NORMALIZED:
        return "no"
    # emoji-prefixed variants
    if norm.endswith(" да") or norm.startswith("да "):
        return "yes"
    if norm.endswith(" нет") or norm.startswith("нет "):
        return "no"
    return "unknown"


def parse_extra_costs_line(text: str) -> dict[str, object]:
    """
    Support:
      100              → other_cost / delivery_cost as single total
      800 1200 500 200 → delivery customs repair advertising
    """
    from decimal import Decimal, InvalidOperation

    stripped = (text or "").strip()
    if not stripped or stripped == "-":
        return {}
    parts = stripped.split()
    labels = ("delivery_cost", "customs_cost", "repair_cost", "advertising_cost")
    out: dict[str, object] = {}
    try:
        if len(parts) == 1:
            out["delivery_cost"] = Decimal(parts[0].replace(",", "."))
            out["extra_costs_total"] = out["delivery_cost"]
            return out
        for idx, label in enumerate(labels):
            if idx < len(parts):
                out[label] = Decimal(parts[idx].replace(",", "."))
        return out
    except InvalidOperation as exc:
        raise ValueError("invalid_extra_costs") from exc
