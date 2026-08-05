"""Feature flags referenced by menu / vertical catalogs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureDef:
    id: str
    title: str
    enabled_by_default: bool = True


FEATURE_REGISTRY: dict[str, FeatureDef] = {
    "core_hr": FeatureDef("core_hr", "Company Core HR"),
    "kpi": FeatureDef("kpi", "KPI dashboards"),
    "otc": FeatureDef("otc", "Crypto OTC desks"),
    "rates": FeatureDef("rates", "Rate channels"),
    "engineering": FeatureDef("engineering", "Drone engineering"),
    "trading": FeatureDef("trading", "Agro trading"),
    "logistics": FeatureDef("logistics", "Logistics"),
    "booking": FeatureDef("booking", "Beauty/cafe booking"),
    "loyalty": FeatureDef("loyalty", "Loyalty programs"),
    "contracts": FeatureDef("contracts", "Legal contracts"),
    "dealer": FeatureDef("dealer", "Auto dealer portal"),
    "vin": FeatureDef("vin", "VIN engine"),
    "leads": FeatureDef("leads", "Lead automation"),
    "mrp": FeatureDef("mrp", "Manufacturing MRP"),
    "sites": FeatureDef("sites", "Construction sites"),
    "clinic": FeatureDef("clinic", "Medical clinic"),
    "agent_store": FeatureDef("agent_store", "AI agent marketplace", enabled_by_default=False),
}


def all_features() -> list[FeatureDef]:
    return list(FEATURE_REGISTRY.values())


def is_feature_enabled(feature_id: str, overrides: dict[str, bool] | None = None) -> bool:
    if overrides and feature_id in overrides:
        return bool(overrides[feature_id])
    feat = FEATURE_REGISTRY.get(feature_id)
    return bool(feat.enabled_by_default) if feat else True
