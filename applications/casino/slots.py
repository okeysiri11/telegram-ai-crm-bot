"""Odessa Gold slots — server-authoritative 5x3 reels. Clients cannot supply symbols."""

from __future__ import annotations

import secrets
from typing import Any

MACHINE_ID = "odessa-gold"
ROWS = 3
REELS = 5

# Weighted reel strip. Higher weight = more common.
SYMBOLS: tuple[tuple[str, int, str], ...] = (
    ("CHERRY", 18, "Вишня"),
    ("ANCHOR", 14, "Якорь"),
    ("WAVE", 14, "Волна"),
    ("BAR", 10, "BAR"),
    ("SEVEN", 8, "7"),
    ("WILD", 6, "WILD"),
    ("ODESSA", 4, "Odessa"),
    ("CROWN", 3, "Корона"),
)

PAY_3 = 2
PAY_4 = 8
PAY_5 = 25
ODESSA_3 = 10
ODESSA_4 = 40
ODESSA_5 = 100


def _strip() -> tuple[str, ...]:
    bag: list[str] = []
    for name, weight, _label in SYMBOLS:
        bag.extend([name] * weight)
    return tuple(bag)


STRIP = _strip()


def spin_reels() -> list[list[str]]:
    """Cryptographic 5-reel x 3-row grid. Independent of client input."""
    grid: list[list[str]] = []
    for _reel in range(REELS):
        start = secrets.randbelow(len(STRIP))
        column = [STRIP[(start + row) % len(STRIP)] for row in range(ROWS)]
        grid.append(column)
    return grid


def _lines(grid: list[list[str]]) -> list[list[str]]:
    mid = [grid[c][1] for c in range(REELS)]
    top = [grid[c][0] for c in range(REELS)]
    bot = [grid[c][2] for c in range(REELS)]
    vee = [grid[0][0], grid[1][1], grid[2][2], grid[3][1], grid[4][0]]
    inv = [grid[0][2], grid[1][1], grid[2][0], grid[3][1], grid[4][2]]
    return [mid, top, bot, vee, inv]


def _match_len(line: list[str]) -> tuple[str, int]:
    first = line[0]
    count = 1
    for symbol in line[1:]:
        if symbol == first or symbol == "WILD" or first == "WILD":
            if first == "WILD" and symbol != "WILD":
                first = symbol
            count += 1
        else:
            break
    return first, count


def line_payout(line: list[str], wager: int) -> int:
    symbol, count = _match_len(line)
    if count < 3:
        return 0
    if symbol in {"ODESSA", "CROWN"}:
        table = {3: ODESSA_3, 4: ODESSA_4, 5: ODESSA_5}
    else:
        table = {3: PAY_3, 4: PAY_4, 5: PAY_5}
    return int(wager * table[count])


def evaluate(grid: list[list[str]], wager: int) -> dict[str, Any]:
    lines = _lines(grid)
    wins = [line_payout(line, wager) for line in lines]
    payout = sum(wins)
    return {
        "reels": grid,
        "line_payouts": wins,
        "payout_chips": payout,
        "outcome": "win" if payout else "lose",
        "machine": MACHINE_ID,
        "server_authoritative": True,
    }


def reject_client_reels(payload: dict[str, Any] | None) -> None:
    if not payload:
        return
    forbidden = {
        "reels",
        "symbols",
        "grid",
        "payout",
        "payout_chips",
        "outcome",
        "line_payouts",
        "result",
    }
    for key in forbidden:
        if key in payload and payload[key] is not None:
            raise ValueError("client cannot supply slot reels or result")
