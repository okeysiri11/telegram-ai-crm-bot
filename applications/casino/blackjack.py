"""Blackjack — server-authoritative 6-deck shoe. Clients cannot supply cards."""

from __future__ import annotations

import secrets
from typing import Any

RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = ("s", "h", "d", "c")
DECKS = 6
BLACKJACK_PAYOUT = 2.5  # stake returned + 3:2
WIN_PAYOUT = 2.0
ACTIONS = frozenset({"hit", "stand", "double"})


def _card(rank: str, suit: str) -> dict[str, str]:
    return {"rank": rank, "suit": suit}


def build_shoe() -> list[dict[str, str]]:
    cards = [_card(rank, suit) for _ in range(DECKS) for rank in RANKS for suit in SUITS]
    for index in range(len(cards) - 1, 0, -1):
        swap = secrets.randbelow(index + 1)
        cards[index], cards[swap] = cards[swap], cards[index]
    return cards


def draw(shoe: list[dict[str, str]]) -> dict[str, str]:
    if not shoe:
        shoe.extend(build_shoe())
    return shoe.pop()


def card_value(rank: str) -> int:
    if rank == "A":
        return 11
    if rank in {"J", "Q", "K"}:
        return 10
    return int(rank)


def hand_total(cards: list[dict[str, str]]) -> int:
    total = 0
    aces = 0
    for card in cards:
        if card.get("hidden"):
            continue
        rank = str(card.get("rank") or "")
        if rank == "?":
            continue
        total += card_value(rank)
        if rank == "A":
            aces += 1
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_blackjack(cards: list[dict[str, str]]) -> bool:
    return len(cards) == 2 and hand_total(cards) == 21


def public_cards(cards: list[dict[str, str]], *, hide_hole: bool) -> list[dict[str, Any]]:
    if not hide_hole or len(cards) < 2:
        return [dict(c) for c in cards]
    shown = [dict(cards[0]), {"rank": "?", "suit": "?", "hidden": True}]
    return shown


def settle_outcome(*, player: list[dict[str, str]], dealer: list[dict[str, str]], wager: int) -> dict[str, Any]:
    p_total = hand_total(player)
    d_total = hand_total(dealer)
    p_bj = is_blackjack(player)
    d_bj = is_blackjack(dealer)
    if p_total > 21:
        outcome, payout = "lose", 0
    elif d_total > 21:
        outcome, payout = "win", int(wager * WIN_PAYOUT)
    elif p_bj and not d_bj:
        outcome, payout = "blackjack", int(wager * BLACKJACK_PAYOUT)
    elif d_bj and not p_bj:
        outcome, payout = "lose", 0
    elif p_total > d_total:
        outcome, payout = "win", int(wager * WIN_PAYOUT)
    elif p_total < d_total:
        outcome, payout = "lose", 0
    else:
        outcome, payout = "push", int(wager)
    return {
        "outcome": outcome,
        "payout_chips": payout,
        "player_total": p_total,
        "dealer_total": d_total,
        "server_authoritative": True,
    }


def play_dealer(shoe: list[dict[str, str]], dealer: list[dict[str, str]]) -> list[dict[str, str]]:
    while hand_total(dealer) < 17:
        dealer.append(draw(shoe))
    return dealer


def reject_client_cards(payload: dict[str, Any] | None) -> None:
    if not payload:
        return
    forbidden = {
        "cards",
        "player_cards",
        "dealer_cards",
        "shoe",
        "total",
        "outcome",
        "payout",
        "payout_chips",
        "result",
    }
    for key in forbidden:
        if key in payload and payload[key] is not None:
            raise ValueError("client cannot supply blackjack cards or result")


def new_hand(*, player_id: str, venue_id: str, wager: int, hand_id: str) -> dict[str, Any]:
    shoe = build_shoe()
    player = [draw(shoe), draw(shoe)]
    dealer = [draw(shoe), draw(shoe)]
    entropy = secrets.token_hex(16)
    status = "player_turn"
    settlement = None
    if is_blackjack(player) or is_blackjack(dealer):
        settlement = settle_outcome(player=player, dealer=dealer, wager=wager)
        status = "settled"
    return {
        "hand_id": hand_id,
        "game": "blackjack",
        "player_id": player_id,
        "venue_id": venue_id,
        "wager_chips": wager,
        "player_cards": player,
        "dealer_cards": dealer,
        "shoe": shoe,
        "status": status,
        "settled": status == "settled",
        "entropy_hex": entropy,
        "server_authoritative": True,
        "settlement": settlement,
    }


def apply_action(hand: dict[str, Any], action: str) -> dict[str, Any]:
    kind = (action or "").strip().lower()
    if kind not in ACTIONS:
        raise ValueError(f"unsupported blackjack action: {action!r}")
    if hand.get("settled"):
        return hand
    if hand.get("status") != "player_turn":
        raise ValueError("hand is not accepting player actions")
    shoe = list(hand["shoe"])
    player = list(hand["player_cards"])
    dealer = list(hand["dealer_cards"])
    if kind == "hit":
        player.append(draw(shoe))
        hand["player_cards"] = player
        hand["shoe"] = shoe
        if hand_total(player) >= 21:
            return _finish(hand, shoe, player, dealer)
        return hand
    if kind == "double":
        if len(player) != 2:
            raise ValueError("double is only allowed on the first two cards")
        player.append(draw(shoe))
        hand["doubled"] = True
        return _finish(hand, shoe, player, dealer)
    return _finish(hand, shoe, player, dealer)


def _finish(
    hand: dict[str, Any],
    shoe: list[dict[str, str]],
    player: list[dict[str, str]],
    dealer: list[dict[str, str]],
) -> dict[str, Any]:
    if hand_total(player) <= 21:
        dealer = play_dealer(shoe, dealer)
    settlement = settle_outcome(player=player, dealer=dealer, wager=int(hand["wager_chips"]))
    hand["player_cards"] = player
    hand["dealer_cards"] = dealer
    hand["shoe"] = shoe
    hand["status"] = "settled"
    hand["settled"] = True
    hand["settlement"] = settlement
    return hand


def public_hand(hand: dict[str, Any]) -> dict[str, Any]:
    hide = not bool(hand.get("settled"))
    settlement = hand.get("settlement") if hand.get("settled") else None
    return {
        "hand_id": hand["hand_id"],
        "game": "blackjack",
        "status": hand["status"],
        "settled": bool(hand.get("settled")),
        "wager_chips": int(hand["wager_chips"]),
        "player_cards": [dict(c) for c in hand["player_cards"]],
        "dealer_cards": public_cards(hand["dealer_cards"], hide_hole=hide),
        "player_total": hand_total(hand["player_cards"]),
        "dealer_total": None if hide else hand_total(hand["dealer_cards"]),
        "available_actions": []
        if hand.get("settled")
        else (["hit", "stand", "double"] if len(hand.get("player_cards") or []) == 2 else ["hit", "stand"]),
        "settlement": settlement,
        "server_authoritative": True,
        "duplicate_settlement_guard": True,
    }
