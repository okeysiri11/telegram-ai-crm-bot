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
DOZEN_PAYOUT = 2

EVEN_MONEY_TYPES = frozenset({"red", "black", "even", "odd", "low", "high"})
DOZEN_TYPES = frozenset({"dozen_1", "dozen_2", "dozen_3", "column_1", "column_2", "column_3"})
ALLOWED_BET_TYPES = frozenset({"straight"}) | EVEN_MONEY_TYPES | DOZEN_TYPES

EUROPEAN_WHEEL_ORDER = (
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
    5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26,
)


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
        "wheel_order": list(EUROPEAN_WHEEL_ORDER),
        "server_authoritative": True,
    }


def resolve_bet_numbers(bet_type: str, numbers: list[int] | None) -> list[int]:
    kind = (bet_type or "").strip().lower().replace(" ", "_")
    aliases = {
        "1-18": "low",
        "19-36": "high",
        "first12": "dozen_1",
        "second12": "dozen_2",
        "third12": "dozen_3",
        "1st12": "dozen_1",
        "2nd12": "dozen_2",
        "3rd12": "dozen_3",
    }
    kind = aliases.get(kind, kind)
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
    if kind == "low":
        return list(range(1, 19))
    if kind == "high":
        return list(range(19, 37))
    if kind == "dozen_1":
        return list(range(1, 13))
    if kind == "dozen_2":
        return list(range(13, 25))
    if kind == "dozen_3":
        return list(range(25, 37))
    if kind == "column_1":
        return [n for n in range(1, 37) if n % 3 == 1]
    if kind == "column_2":
        return [n for n in range(1, 37) if n % 3 == 2]
    if kind == "column_3":
        return [n for n in range(1, 37) if n % 3 == 0]
    raise ValueError(f"unsupported bet type: {bet_type!r}")


def payout_multiplier(bet_type: str) -> int:
    kind = (bet_type or "").strip().lower().replace(" ", "_")
    aliases = {"1-18": "low", "19-36": "high"}
    kind = aliases.get(kind, kind)
    if kind == "straight":
        return STRAIGHT_PAYOUT
    if kind in EVEN_MONEY_TYPES:
        return EVEN_MONEY_PAYOUT
    if kind in DOZEN_TYPES:
        return DOZEN_PAYOUT
    raise ValueError(f"unsupported bet type: {bet_type!r}")


def settle_bet(*, bet_type: str, numbers: list[int], amount_chips: int, result_number: int) -> int:
    """Return chips credited on win (stake + profit). Loss returns 0."""
    if amount_chips <= 0:
        return 0
    covered = resolve_bet_numbers(bet_type, numbers)
    if result_number not in covered:
        return 0
    return amount_chips + amount_chips * payout_multiplier(bet_type)
