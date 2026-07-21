# Export/logistics AI hooks — Platform + Ecosystem bridges only.

from __future__ import annotations

import logging
from typing import Any

from applications.agro_marketplace.export.models import (
    Carrier,
    Container,
    InternationalExportShipment,
    RoutePlan,
)
from applications.agro_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge

logger = logging.getLogger(__name__)


class ExportAIIntegration:
    def __init__(
        self,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self._platform = platform or platform_bridge
        self._ecosystem = ecosystem or ecosystem_bridge

    async def optimize_route(
        self,
        origin: str,
        destination: str,
        candidates: list[RoutePlan],
    ) -> dict[str, Any]:
        if not candidates:
            return {"route_id": "", "estimated_days": 0, "score": 0.0}
        best = min(candidates, key=lambda r: (r.estimated_days or 999, r.distance_nm or 99999))
        await self._platform.start_ai_workflow(
            "route_optimization",
            {"origin": origin, "destination": destination, "route_id": best.route_id},
        )
        return {
            "route_id": best.route_id,
            "estimated_days": best.estimated_days,
            "distance_nm": best.distance_nm,
            "score": 100.0 - best.estimated_days,
        }

    async def recommend_carrier(
        self,
        destination_country: str,
        carriers: list[Carrier],
        *,
        mode: str = "sea",
    ) -> list[dict[str, Any]]:
        scored = []
        for carrier in carriers:
            score = carrier.rating
            if destination_country in carrier.countries:
                score += 2.0
            if carrier.mode == mode:
                score += 1.0
            scored.append((score, carrier))
        scored.sort(key=lambda x: x[0], reverse=True)
        await self._ecosystem.invoke_workforce(
            "carrier_recommendation",
            context={"destination_country": destination_country, "mode": mode},
        )
        return [c.to_dict() | {"match_score": round(s, 2)} for s, c in scored[:5]]

    async def assess_export_risk(self, shipment: InternationalExportShipment) -> dict[str, Any]:
        reasons: list[str] = []
        score = 0.15
        if not shipment.document_ids:
            score += 0.25
            reasons.append("missing_export_documents")
        if not shipment.container_ids:
            score += 0.2
            reasons.append("no_containers_assigned")
        if not shipment.carrier_id:
            score += 0.15
            reasons.append("no_carrier")
        if shipment.destination_country.lower() in {"sanctioned", "high_risk"}:
            score += 0.3
            reasons.append("destination_risk")
        # Knowledge / governance hooks
        regs = self._ecosystem.knowledge_lookup(f"export {shipment.destination_country}")
        if not regs:
            score += 0.05
            reasons.append("limited_regulation_knowledge")
        self._ecosystem.check_governance(
            "export_shipment",
            {"shipment_id": shipment.shipment_id, "country": shipment.destination_country},
        )
        await self._platform.recommend_products(
            {"hook": "export_risk", "shipment_id": shipment.shipment_id, "score": score}
        )
        return {"risk_score": round(min(1.0, score), 2), "reasons": reasons, "high_risk": score >= 0.5}

    async def predict_delivery(
        self,
        shipment: InternationalExportShipment,
        route: RoutePlan | None,
    ) -> dict[str, Any]:
        days = route.estimated_days if route else 21
        if shipment.incoterm.value in {"CIF", "DDP"}:
            days += 2
        return {
            "shipment_id": shipment.shipment_id,
            "predicted_transit_days": days,
            "confidence": 0.65 if route else 0.4,
        }

    async def optimize_shipment(self, shipment: InternationalExportShipment) -> dict[str, Any]:
        actions = []
        if not shipment.route_id:
            actions.append("assign_route")
        if not shipment.carrier_id:
            actions.append("assign_carrier")
        if not shipment.container_ids:
            actions.append("allocate_containers")
        if len(shipment.document_ids) < 3:
            actions.append("prepare_documents")
        return {"shipment_id": shipment.shipment_id, "actions": actions, "priority": len(actions)}

    async def optimize_container(self, container: Container, load_tons: float, volume_cbm: float) -> dict[str, Any]:
        weight_ok = container.used_weight_tons + load_tons <= container.max_weight_tons
        volume_ok = container.used_cbm + volume_cbm <= container.capacity_cbm
        utilization = 0.0
        if container.capacity_cbm:
            utilization = (container.used_cbm + volume_cbm) / container.capacity_cbm
        return {
            "container_id": container.container_id,
            "fits": weight_ok and volume_ok,
            "projected_utilization": round(min(1.0, utilization), 2),
            "suggestion": "load" if weight_ok and volume_ok else "split_or_upgrade",
        }

    async def validate_customs_documents(
        self,
        shipment: InternationalExportShipment,
        documents: list[dict[str, Any]],
        required: list[str],
    ) -> dict[str, Any]:
        present = {d.get("document_type") for d in documents}
        missing = [r for r in required if r not in present]
        unverified = [d.get("document_id") for d in documents if not d.get("verified")]
        await self._platform.start_ai_workflow(
            "customs_validation",
            {"shipment_id": shipment.shipment_id, "missing": missing},
        )
        return {
            "valid": not missing and not unverified,
            "missing": missing,
            "unverified": unverified,
        }

    async def trade_opportunities(self, destination_country: str) -> list[dict[str, Any]]:
        knowledge = self._ecosystem.knowledge_lookup(f"export market {destination_country}")
        return [
            {
                "destination_country": destination_country,
                "opportunity": "agricultural_export",
                "knowledge_hits": len(knowledge),
                "suggested_incoterms": ["FOB", "CIF"],
            }
        ]


export_ai = ExportAIIntegration()
