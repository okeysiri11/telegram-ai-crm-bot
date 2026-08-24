"""VIN normalize + validate. Never silently rewrite historical invalid records."""

from __future__ import annotations

import re
from typing import Any

_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
_STRIP_RE = re.compile(r"[\s\-]+")


def normalize_vin(value: Any) -> str:
    raw = str(value or "").strip().upper()
    return _STRIP_RE.sub("", raw)


def validate_vin(vin: str, *, allow_nonstandard: bool = False) -> dict[str, Any] | None:
    """Return error dict if invalid, else None.

    Standard VIN is ISO 3779 (17 chars, no I/O/Q). Non-standard values are
    accepted only when an authorized admin explicitly allows the conflict.
    Empty VIN is not allowed for new vehicles.
    """
    if not vin:
        return {
            "ok": False,
            "error": "validation",
            "message_ru": "Укажите VIN",
            "field": "vin",
        }
    if len(vin) == 17 and _VIN_RE.match(vin):
        return None
    if allow_nonstandard:
        if 5 <= len(vin) <= 32:
            return None
        return {
            "ok": False,
            "error": "validation",
            "message_ru": "Нестандартный VIN слишком короткий или длинный",
            "field": "vin",
        }
    if len(vin) != 17:
        return {
            "ok": False,
            "error": "validation",
            "message_ru": "Стандартный VIN — 17 символов. Нестандартный VIN может сохранить только директор или администратор.",
            "field": "vin",
            "code": "nonstandard_vin",
        }
    return {
        "ok": False,
        "error": "validation",
        "message_ru": "VIN содержит недопустимые символы (I, O, Q запрещены)",
        "field": "vin",
    }
