"""Casino vertical configuration — play-money only (Sprint 15–20)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CasinoConfig:
    application_name: str = "Odessa Prime Casino"
    application_version: str = "20.0.0-play-money"
    api_prefix: str = "/api/casino/v1"
    currency_code: str = "CHIPS"
    currency_label: str = "PLAY"
    display_currency: str = "DEMO CHIPS"
    opening_chips: int = 10_000
    min_wager: int = 1
    max_wager: int = 10_000
    chip_denoms: tuple[int, ...] = (10, 50, 100, 500, 1_000, 5_000)
    demo_grant_chips: int = 5_000
    demo_grant_cooldown_seconds: int = 900
    demo_grant_balance_cap: int = 25_000
    betting_open_seconds: int = 18
    betting_closing_seconds: int = 3
    play_money_only: bool = True
    real_money_implemented: bool = False
    payment_processing_implemented: bool = False
    default_venue_id: str = "odessa-prime"
    city_building_id: str = "casino"


DEFAULT_CONFIG = CasinoConfig()
