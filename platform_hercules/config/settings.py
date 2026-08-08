"""Hercules configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HerculesConfig:
    max_concurrent: int = int(os.environ.get("HERCULES_MAX_CONCURRENT", "32"))
    rate_limit_per_min: int = int(os.environ.get("HERCULES_RATE_LIMIT", "120"))
    sandbox: bool = os.environ.get("HERCULES_SANDBOX", "1") != "0"
    locale: str = "ru"


hercules_config = HerculesConfig()
