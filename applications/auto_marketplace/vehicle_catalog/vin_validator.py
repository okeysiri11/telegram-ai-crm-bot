# VIN validation.

from __future__ import annotations

import re

_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
_TRANSLITERATION = {
    **{str(i): i for i in range(10)},
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}
_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)


def normalize_vin(vin: str) -> str:
    return (vin or "").strip().upper()


def validate_vin(vin: str, *, check_digit: bool = True) -> tuple[bool, str]:
    normalized = normalize_vin(vin)
    if not normalized:
        return False, "VIN is required"
    if len(normalized) != 17:
        return False, "VIN must be 17 characters"
    if not _VIN_PATTERN.match(normalized):
        return False, "VIN contains invalid characters"
    if not check_digit:
        return True, "valid"
    total = sum(_TRANSLITERATION[c] * _WEIGHTS[i] for i, c in enumerate(normalized))
    check = total % 11
    expected = "X" if check == 10 else str(check)
    if normalized[8] != expected:
        return False, f"Invalid VIN check digit (expected {expected})"
    return True, "valid"
