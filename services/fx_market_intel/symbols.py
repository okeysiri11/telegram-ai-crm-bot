"""Symbol normalization for FX / DXY desk."""

from __future__ import annotations

ALIASES = {
    "EURUSD": "EUR/USD",
    "EUR/USD": "EUR/USD",
    "EUR-USD": "EUR/USD",
    "DXY": "DXY",
    "DX": "DXY",
    "USDX": "DXY",
    "DOLLAR INDEX": "DXY",
    "USD INDEX": "DXY",
}

CORE_INSTRUMENTS = ("EUR/USD", "DXY")


def normalize_symbol(raw: str) -> str:
    key = (raw or "").strip().upper().replace(" ", "")
    if not key:
        return ""
    spaced = key.replace("-", "/")
    if spaced in ALIASES:
        return ALIASES[spaced]
    compact = key.replace("/", "").replace("-", "")
    if compact in ALIASES:
        return ALIASES[compact]
    if "/" in spaced:
        parts = spaced.split("/")
        if len(parts) == 2:
            return f"{parts[0]}/{parts[1]}"
    return spaced or key


def is_core_instrument(symbol: str) -> bool:
    return normalize_symbol(symbol) in CORE_INSTRUMENTS
