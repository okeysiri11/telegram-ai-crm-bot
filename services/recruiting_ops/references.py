"""Vanguard public application reference numbers (VG-XXXXXX)."""

from __future__ import annotations

import secrets

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_vanguard_reference() -> str:
    return "VG-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))
