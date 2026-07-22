"""Production AI — manufacturing assistance (Sprint 11.6)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.engineering_suite_ai import EngineeringSuiteAIAssistant


PRODUCTION_AI_CAPABILITIES = (
    "detect_assembly_mistakes",
    "suggest_replacements",
    "predict_production_delays",
    "optimize_inventory",
    "optimize_assembly_sequence",
    "recommend_suppliers",
    "estimate_manufacturing_cost",
    "predict_production_failures",
    "generate_production_reports",
)


class ProductionAIAssistant(EngineeringSuiteAIAssistant):
    def capabilities(self) -> list[str]:
        return list(dict.fromkeys([*super().capabilities(), *PRODUCTION_AI_CAPABILITIES]))

    def detect_assembly_mistakes(self, *, observations: list[str] | None = None) -> dict[str, Any]:
        obs = list(observations or [])
        mistakes = []
        for o in obs:
            low = o.lower()
            if "torque" in low:
                mistakes.append("Incorrect fastener torque")
            if "polarity" in low or "reverse" in low:
                mistakes.append("Power polarity / motor direction issue")
            if "missing" in low:
                mistakes.append("Missing component on assembly")
        response = {"observations": obs, "mistakes": mistakes or ["No clear assembly mistakes detected"], "ok": not mistakes}
        return self._session(agent="detect_assembly_mistakes", query="assembly", context={"observations": obs}, response=response)

    def suggest_replacements(self, *, sku: str, reason: str = "unavailable") -> dict[str, Any]:
        response = {
            "sku": sku,
            "reason": reason,
            "suggestions": [f"{sku}-ALT1", f"{sku}-COMPAT"],
            "policy": "Validate form-fit-function before substitution",
        }
        return self._session(agent="suggest_replacements", query=sku, context=response, response=response)

    def predict_production_delays(self, *, open_orders: int, missing_parts: int, capacity: int) -> dict[str, Any]:
        risk = "low"
        days = 1
        if missing_parts > 0:
            risk = "high"
            days = 5 + missing_parts
        elif open_orders > capacity * 2:
            risk = "medium"
            days = 3
        response = {"open_orders": open_orders, "missing_parts": missing_parts, "capacity": capacity, "delay_risk": risk, "est_extra_days": days}
        return self._session(agent="predict_production_delays", query="delays", context=response, response=response)

    def optimize_inventory(self, *, levels: dict[str, int], targets: dict[str, int] | None = None) -> dict[str, Any]:
        targets = dict(targets or {})
        actions = []
        for sku, qty in levels.items():
            target = targets.get(sku, 10)
            if qty < target:
                actions.append({"sku": sku, "action": "reorder", "qty": target - qty})
        response = {"actions": actions, "count": len(actions)}
        return self._session(agent="optimize_inventory", query="inventory", context={"levels": levels}, response=response)

    def optimize_assembly_sequence(self, *, steps: list[str]) -> dict[str, Any]:
        # Prefer prep → mounts → electronics → wiring → props last
        priority = {"frame_prep": 0, "motor_mount": 1, "esc_install": 2, "fc_install": 3, "wiring": 4, "payload_mount": 5, "prop_install": 6, "final_torque": 7}
        ordered = sorted(steps, key=lambda s: priority.get(s, 50))
        response = {"original": steps, "optimized": ordered}
        return self._session(agent="optimize_assembly_sequence", query="sequence", context={"steps": steps}, response=response)

    def recommend_suppliers(self, *, component_type: str, suppliers: list[str] | None = None) -> dict[str, Any]:
        response = {
            "component_type": component_type,
            "recommended": list(suppliers or ["Primary Electronics Co", "UAV Parts Ltd"]),
            "criteria": ["lead_time", "quality", "traceability"],
        }
        return self._session(agent="recommend_suppliers", query=component_type, context=response, response=response)

    def estimate_manufacturing_cost(self, *, bom_cost: float, labor_hours: float, labor_rate: float = 50.0, overhead: float = 0.15) -> dict[str, Any]:
        labor = labor_hours * labor_rate
        subtotal = bom_cost + labor
        total = subtotal * (1 + overhead)
        response = {"bom_cost": bom_cost, "labor": labor, "overhead": overhead, "total_cost": round(total, 2)}
        return self._session(agent="estimate_manufacturing_cost", query="cost", context=response, response=response)

    def predict_production_failures(self, *, signals: list[str] | None = None) -> dict[str, Any]:
        signals = list(signals or [])
        predictions = []
        if "solder_void" in signals:
            predictions.append("Intermittent power fault")
        if "imbalance" in signals:
            predictions.append("Vibration / bearing wear")
        response = {"signals": signals, "predictions": predictions or ["No dominant production failure predicted"]}
        return self._session(agent="predict_production_failures", query="failures", context={"signals": signals}, response=response)

    def generate_production_reports(self, *, summary: dict[str, Any]) -> dict[str, Any]:
        response = {
            "summary": summary,
            "report": {
                "title": "Production Summary",
                "sections": ["orders", "assemblies", "qa", "shipments"],
                "generated": True,
            },
        }
        return self._session(agent="generate_production_reports", query="report", context=summary, response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        key = agent.lower().replace("-", "_")
        dispatch = {
            "detect_assembly_mistakes": lambda: self.detect_assembly_mistakes(observations=ctx.get("observations") or [query]),
            "suggest_replacements": lambda: self.suggest_replacements(sku=query or ctx.get("sku", ""), reason=ctx.get("reason", "unavailable")),
            "predict_production_delays": lambda: self.predict_production_delays(
                open_orders=int(ctx.get("open_orders", 5)),
                missing_parts=int(ctx.get("missing_parts", 0)),
                capacity=int(ctx.get("capacity", 3)),
            ),
            "optimize_inventory": lambda: self.optimize_inventory(levels=ctx.get("levels") or {}, targets=ctx.get("targets")),
            "optimize_assembly_sequence": lambda: self.optimize_assembly_sequence(steps=ctx.get("steps") or []),
            "recommend_suppliers": lambda: self.recommend_suppliers(component_type=query or "motors", suppliers=ctx.get("suppliers")),
            "estimate_manufacturing_cost": lambda: self.estimate_manufacturing_cost(
                bom_cost=float(ctx.get("bom_cost", 100)),
                labor_hours=float(ctx.get("labor_hours", 4)),
                labor_rate=float(ctx.get("labor_rate", 50)),
                overhead=float(ctx.get("overhead", 0.15)),
            ),
            "predict_production_failures": lambda: self.predict_production_failures(signals=ctx.get("signals") or [query]),
            "generate_production_reports": lambda: self.generate_production_reports(summary=ctx.get("summary") or {"query": query}),
        }
        if key in dispatch:
            return dispatch[key]()
        return super().assist(agent=agent, query=query, context=context)


from applications.drone_platform.shared.store import drone_store

production_ai = ProductionAIAssistant(store=drone_store)
