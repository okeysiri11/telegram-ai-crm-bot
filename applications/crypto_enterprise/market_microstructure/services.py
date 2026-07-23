"""AI market interpretation, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

DASHBOARD_TYPES = ["order_flow", "derivatives", "liquidity", "liquidation", "ai_market"]
REGISTRY_TYPES = ["microstructure", "order_book", "derivatives", "liquidity", "trade_flow"]
BIAS_SIDES = ["long", "short", "neutral"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIMarketInterpretation:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def market_structure(self, *, symbol: str, structure: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        mid = _id("mm_aistr")
        return self.store.mm_ai_structure.save(
            mid,
            {
                "analysis_id": mid,
                "symbol": symbol.upper(),
                "structure": structure or "range",
                "score": score,
                "at": _now(),
            },
        )

    def institutional(self, *, symbol: str, intensity: float) -> dict[str, Any]:
        iid = _id("mm_ainst")
        return self.store.mm_ai_institutional.save(
            iid,
            {
                "detection_id": iid,
                "symbol": symbol.upper(),
                "intensity": float(intensity),
                "detected": intensity >= 0.55,
                "at": _now(),
            },
        )

    def whale(self, *, symbol: str, size_usd: float, side: str) -> dict[str, Any]:
        wid = _id("mm_awhale")
        return self.store.mm_ai_whale.save(
            wid,
            {
                "detection_id": wid,
                "symbol": symbol.upper(),
                "size_usd": float(size_usd),
                "side": side,
                "at": _now(),
            },
        )

    def momentum_shift(self, *, symbol: str, from_bias: str, to_bias: str) -> dict[str, Any]:
        mid = _id("mm_amom")
        return self.store.mm_ai_momentum.save(
            mid,
            {
                "shift_id": mid,
                "symbol": symbol.upper(),
                "from_bias": from_bias,
                "to_bias": to_bias,
                "at": _now(),
            },
        )

    def trend_continuation(self, *, symbol: str, probability: float) -> dict[str, Any]:
        probability = float(probability)
        if probability < 0 or probability > 1:
            raise ValidationError("probability must be 0..1")
        tid = _id("mm_acont")
        return self.store.mm_ai_continuation.save(
            tid,
            {
                "analysis_id": tid,
                "symbol": symbol.upper(),
                "probability": probability,
                "at": _now(),
            },
        )

    def reversal(self, *, symbol: str, probability: float) -> dict[str, Any]:
        probability = float(probability)
        if probability < 0 or probability > 1:
            raise ValidationError("probability must be 0..1")
        rid = _id("mm_arev")
        return self.store.mm_ai_reversal.save(
            rid,
            {
                "analysis_id": rid,
                "symbol": symbol.upper(),
                "probability": probability,
                "at": _now(),
            },
        )

    def trade_bias(self, *, symbol: str, bias: str, confidence: float) -> dict[str, Any]:
        if bias not in BIAS_SIDES:
            raise ValidationError("bias must be long|short|neutral")
        confidence = float(confidence)
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be 0..1")
        bid = _id("mm_abias")
        return self.store.mm_ai_bias.save(
            bid,
            {
                "bias_id": bid,
                "symbol": symbol.upper(),
                "bias": bias,
                "confidence": confidence,
                "at": _now(),
            },
        )

    def confidence_score(self, *, symbol: str, score: float, drivers: list[str] | None = None) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        cid = _id("mm_aconf")
        return self.store.mm_ai_confidence.save(
            cid,
            {
                "score_id": cid,
                "symbol": symbol.upper(),
                "score": score,
                "drivers": drivers or [],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "structure": self.store.mm_ai_structure.count(),
            "bias": self.store.mm_ai_bias.count(),
            "confidence": self.store.mm_ai_confidence.count(),
            "whale": self.store.mm_ai_whale.count(),
        }


class MicrostructureDashboard:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "order_flow") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "order_flow": {
                "order_books": self.store.mm_order_books.count(),
                "time_sales": self.store.mm_time_sales.count(),
            },
            "derivatives": {
                "open_interest": self.store.mm_open_interest.count(),
                "funding": self.store.mm_funding.count(),
            },
            "liquidity": {
                "zones": self.store.mm_liq_zones.count(),
                "absorption": self.store.mm_absorption.count(),
            },
            "liquidation": {
                "long_liqs": self.store.mm_long_liqs.count(),
                "short_liqs": self.store.mm_short_liqs.count(),
                "cascades": self.store.mm_cascades.count(),
            },
            "ai_market": {
                "bias": self.store.mm_ai_bias.count(),
                "confidence": self.store.mm_ai_confidence.count(),
            },
        }[dashboard_type]
        did = _id("mm_dash")
        return self.store.mm_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.mm_dashboards.count(), "types": self.types}


class MicrostructureKnowledge:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("mm_reg")
        return self.store.mm_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"mm:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.mm_registries.count(), "types": self.types}
