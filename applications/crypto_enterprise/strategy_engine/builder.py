"""Strategy builder and rule engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

CONDITION_TYPES = [
    "indicator",
    "market_structure",
    "volume",
    "order_flow",
    "sentiment",
    "macro",
]
TEMPLATES = ["trend_follow", "mean_reversion", "breakout", "momentum", "custom"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class StrategyBuilder:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store
        self.condition_types = list(CONDITION_TYPES)
        self.templates = list(TEMPLATES)

    def create_visual(self, *, name: str, nodes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        sid = _id("se_vis")
        return self.store.se_visual.save(
            sid,
            {
                "builder_id": sid,
                "name": name,
                "nodes": nodes or [],
                "kind": "visual",
                "at": _now(),
            },
        )

    def add_rule(
        self,
        *,
        strategy_id: str,
        condition_type: str,
        expression: str,
        timeframe: str = "1h",
    ) -> dict[str, Any]:
        if condition_type not in CONDITION_TYPES:
            raise ValidationError(f"condition_type must be one of {CONDITION_TYPES}")
        if not expression:
            raise ValidationError("expression required")
        rid = _id("se_rule")
        return self.store.se_rules.save(
            rid,
            {
                "rule_id": rid,
                "strategy_id": strategy_id,
                "condition_type": condition_type,
                "expression": expression,
                "timeframe": timeframe,
                "at": _now(),
            },
        )

    def multi_timeframe(self, *, strategy_id: str, timeframes: list[str], logic: str = "and") -> dict[str, Any]:
        if not timeframes:
            raise ValidationError("timeframes required")
        mid = _id("se_mtf")
        return self.store.se_mtf_rules.save(
            mid,
            {
                "mtf_id": mid,
                "strategy_id": strategy_id,
                "timeframes": timeframes,
                "logic": logic,
                "at": _now(),
            },
        )

    def from_template(self, *, template: str, name: str, symbol: str = "BTCUSDT") -> dict[str, Any]:
        if template not in TEMPLATES:
            raise ValidationError(f"template must be one of {TEMPLATES}")
        if not name:
            raise ValidationError("name required")
        tid = _id("se_strat")
        return self.store.se_strategies.save(
            tid,
            {
                "strategy_id": tid,
                "name": name,
                "template": template,
                "symbol": symbol.upper(),
                "status": "draft",
                "at": _now(),
            },
        )

    def register(
        self,
        *,
        name: str,
        symbol: str,
        template: str = "custom",
        rules: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        strategy = self.from_template(template=template, name=name, symbol=symbol)
        for rule in rules or []:
            self.add_rule(
                strategy_id=strategy["strategy_id"],
                condition_type=rule.get("condition_type", "indicator"),
                expression=rule.get("expression", ""),
                timeframe=rule.get("timeframe", "1h"),
            )
        return strategy

    def status(self) -> dict[str, Any]:
        return {
            "strategies": self.store.se_strategies.count(),
            "rules": self.store.se_rules.count(),
            "visual": self.store.se_visual.count(),
            "mtf": self.store.se_mtf_rules.count(),
        }
