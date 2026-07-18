# VIN Engine v1 — validation and offline decoding (ISO 3779).
# Backward-compatible re-export; implementation lives in lib.vin_decoder.

from lib.vin_decoder import (  # noqa: F401
    build_auction_reference,
    build_history_event,
    decode_vin,
    normalize_vin,
    validate_vin,
)

__all__ = [
    "build_auction_reference",
    "build_history_event",
    "decode_vin",
    "normalize_vin",
    "validate_vin",
]
