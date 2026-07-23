"""AI trade intelligence, dashboards, and knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DASHBOARD_TYPES = ["customs", "border", "trade", "compliance", "ai_trade"]
REGISTRY_TYPES = ["trade", "customs", "compliance", "document", "international"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AITradeIntelligence:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def compliance_risk(self, *, party: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        rid = _id("ct_arisk")
        return self.store.ct_ai_risk.save(
            rid,
            {
                "scoring_id": rid,
                "party": party,
                "score": score,
                "band": "high" if score >= 0.7 else "medium" if score >= 0.4 else "low",
                "at": _now(),
            },
        )

    def delay_predict(self, *, declaration_id: str, risk: float) -> dict[str, Any]:
        risk = float(risk)
        if risk < 0 or risk > 1:
            raise ValidationError("risk must be 0..1")
        did = _id("ct_adel")
        return self.store.ct_ai_delay.save(
            did,
            {
                "prediction_id": did,
                "declaration_id": declaration_id,
                "risk": risk,
                "expected_delay_hours": round(risk * 48, 1),
                "at": _now(),
            },
        )

    def validate_document(self, *, document_id: str, valid: bool = True) -> dict[str, Any]:
        vid = _id("ct_aval")
        return self.store.ct_ai_docval.save(
            vid,
            {
                "validation_id": vid,
                "document_id": document_id,
                "valid": bool(valid),
                "confidence": 0.94 if valid else 0.55,
                "at": _now(),
            },
        )

    def optimize_trade(self, *, corridor: str) -> dict[str, Any]:
        oid = _id("ct_aopt")
        return self.store.ct_ai_trade_opt.save(
            oid,
            {
                "optimization_id": oid,
                "corridor": corridor,
                "cost_saving_pct": 7.5,
                "at": _now(),
            },
        )

    def optimize_tariff(self, *, hs_code: str, baseline_rate: float) -> dict[str, Any]:
        oid = _id("ct_atar")
        return self.store.ct_ai_tariff.save(
            oid,
            {
                "optimization_id": oid,
                "hs_code": hs_code,
                "baseline_rate": float(baseline_rate),
                "optimized_rate": round(float(baseline_rate) * 0.92, 4),
                "at": _now(),
            },
        )

    def congestion_predict(self, *, checkpoint_id: str) -> dict[str, Any]:
        cid = _id("ct_acong")
        return self.store.ct_ai_congestion.save(
            cid,
            {
                "prediction_id": cid,
                "checkpoint_id": checkpoint_id,
                "congestion_index": 0.58,
                "wait_minutes": 42,
                "at": _now(),
            },
        )

    def fraud_detect(self, *, trade_ref: str, anomaly_score: float) -> dict[str, Any]:
        score = float(anomaly_score)
        if score < 0 or score > 1:
            raise ValidationError("anomaly_score must be 0..1")
        fid = _id("ct_afraud")
        return self.store.ct_ai_fraud.save(
            fid,
            {
                "detection_id": fid,
                "trade_ref": trade_ref,
                "anomaly_score": score,
                "flagged": score >= 0.6,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "risk_scores": self.store.ct_ai_risk.count(),
            "delay_predictions": self.store.ct_ai_delay.count(),
            "fraud_detections": self.store.ct_ai_fraud.count(),
        }


class CustomsDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "customs") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "customs": {
                "declarations": self.store.ct_declarations.count(),
                "clearances": self.store.ct_clearances.count(),
            },
            "border": {
                "checkpoints": self.store.ct_checkpoints.count(),
                "crossings": self.store.ct_crossings.count(),
            },
            "trade": {
                "imports": self.store.ct_imports.count(),
                "exports": self.store.ct_exports.count(),
            },
            "compliance": {
                "screenings": self.store.ct_sanctions.count(),
                "licenses": self.store.ct_licenses.count(),
            },
            "ai_trade": {
                "risk": self.store.ct_ai_risk.count(),
                "fraud": self.store.ct_ai_fraud.count(),
            },
        }[dashboard_type]
        did = _id("ct_dash")
        return self.store.ct_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ct_dashboards.count(), "types": self.types}


class CustomsKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ct_reg")
        return self.store.ct_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ct:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ct_registries.count(), "types": self.types}
