"""Casino vertical configuration — play-money foundation only (Sprint 15)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CasinoConfig:
    application_name: str = "ADOS Casino"
    application_version: str = "15.0.0-play-money"
    api_prefix: str = "/api/casino/v1"
    currency_code: str = "CHIPS"
    opening_chips: int = 10_000
    min_wager: int = 1
    max_wager: int = 5_000
    play_money_only: bool = True
    real_money_implemented: bool = False
    payment_processing_implemented: bool = False
    default_venue_id: str = "odessa-prime"
    city_building_id: str = "casino"


DEFAULT_CONFIG = CasinoConfig()
