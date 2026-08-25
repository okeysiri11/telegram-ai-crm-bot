"""European roulette — server-authoritative play-money math. No client RNG."""

from __future__ import annotations

import secrets
from typing import Any

RED_NUMBERS = frozenset(
    {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
)
WHEEL_SIZE = 37  # 0-36 inclusive
STRAIGHT_PAYOUT = 35
EVEN_MONEY_PAYOUT = 1

ALLOWED_BET_TYPES = frozenset({"straight", "red", "black", "even", "odd"})


def color_for_number(number: int) -> str:
    if number == 0:
        return "green"
    return "red" if number in RED_NUMBERS else "black"


def spin_european() -> dict[str, Any]:
    """Cryptographic server spin. Clients cannot supply the winning number."""
    entropy = secrets.token_bytes(16)
    number = secrets.randbelow(WHEEL_SIZE)
    return {
        "number": number,
        "color": color_for_number(number),
        "entropy_hex": entropy.hex(),
        "wheel": "european",
        "server_authoritative": True,
    }


def resolve_bet_numbers(bet_type: str, numbers: list[int] | None) -> list[int]:
    kind = (bet_type or "").strip().lower()
    if kind not in ALLOWED_BET_TYPES:
        raise ValueError(f"unsupported bet type: {bet_type!r}")
    if kind == "straight":
        if not numbers or len(numbers) != 1:
            raise ValueError("straight bets require exactly one number")
        n = int(numbers[0])
        if n < 0 or n > 36:
            raise ValueError("straight number must be 0-36")
        return [n]
    if kind == "red":
        return sorted(RED_NUMBERS)
    if kind == "black":
        return [n for n in range(1, 37) if n not in RED_NUMBERS]
    if kind == "even":
        return [n for n in range(2, 37, 2)]
    if kind == "odd":
        return [n for n in range(1, 37, 2)]
    raise ValueError(f"unsupported bet type: {bet_type!r}")


def payout_multiplier(bet_type: str) -> int:
    kind = (bet_type or "").strip().lower()
    if kind == "straight":
        return STRAIGHT_PAYOUT
    if kind in {"red", "black", "even", "odd"}:
        return EVEN_MONEY_PAYOUT
    raise ValueError(f"unsupported bet type: {bet_type!r}")


def settle_bet(*, bet_type: str, numbers: list[int], amount_chips: int, result_number: int) -> int:
    """Return chips credited on win (stake + profit). Loss returns 0."""
    if amount_chips <= 0:
        return 0
    covered = resolve_bet_numbers(bet_type, numbers)
    if result_number not in covered:
        return 0
    return amount_chips + amount_chips * payout_multiplier(bet_type)
