# Shared dealer quote / BidEx parser constants (no engine imports).

from __future__ import annotations

from decimal import Decimal

from config import OWNER_ID
from database.models.dealer_quote_authority_engine import QuotePair, ReferenceSourceCode

BIDEX_RATES_TAG = "#BIDEX_RATES"

BIDEX_SOURCE_AUTHORITY = "bidex_odesa_telegram"
FOMA_SOURCE_AUTHORITY = "foma_rates_telegram"
SOURCE_AUTHORITY = BIDEX_SOURCE_AUTHORITY

DEFAULT_SPREADS: dict[str, Decimal] = {
    "warning_pct": Decimal("1.5"),
    "critical_pct": Decimal("3.0"),
}

DEFAULT_DEVIATION_WARNING_PCT = DEFAULT_SPREADS["warning_pct"]
DEFAULT_DEVIATION_CRITICAL_PCT = DEFAULT_SPREADS["critical_pct"]

SOURCE_TYPES = frozenset(source.value for source in ReferenceSourceCode)

PAIR_DEALER_FIELDS = {
    QuotePair.USD_UAH.value: ("USD_BUY", "USD_SELL"),
    QuotePair.EUR_UAH.value: ("EUR_BUY", "EUR_SELL"),
    QuotePair.USDT_UAH.value: ("USDT_BUY", "USDT_SELL"),
}

__all__ = (
    "BIDEX_RATES_TAG",
    "BIDEX_SOURCE_AUTHORITY",
    "DEFAULT_DEVIATION_CRITICAL_PCT",
    "DEFAULT_DEVIATION_WARNING_PCT",
    "DEFAULT_SPREADS",
    "FOMA_SOURCE_AUTHORITY",
    "OWNER_ID",
    "PAIR_DEALER_FIELDS",
    "SOURCE_AUTHORITY",
    "SOURCE_TYPES",
)
