"""FX market intelligence (EUR/USD + DXY). Canonical Web + Telegram path."""

from __future__ import annotations

from services.fx_market_intel.service import (
    FxMarketIntelService,
    get_fx_market_intel,
    reset_fx_market_intel_for_tests,
)

__all__ = ["FxMarketIntelService", "get_fx_market_intel", "reset_fx_market_intel_for_tests"]
