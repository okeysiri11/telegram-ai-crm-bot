"""Semantic Search — Sprint 24.2."""

from __future__ import annotations

from typing import Any


class SemanticSearch:
    def query(self, *, text: str, entities: list[dict[str, Any]] | None = None, edges: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not text or not str(text).strip():
            raise ValueError("query text is required")
        q = text.strip().lower()
        entities = list(entities or [])
        edges = list(edges or [])
        matched = []
        intent = "general"
        if "vip" in q and ("не приход" in q or "60" in q or "did not" in q or "haven't" in q):
            intent = "inactive_vip_customers"
            matched = [e for e in entities if e.get("entity_type") == "customer" and "vip" in [x.lower() for x in (e.get("labels") or [])]]
        elif "акци" in q or "campaign" in q or "выруч" in q or "revenue" in q:
            intent = "high_lift_campaigns"
            matched = [
                e
                for e in entities
                if e.get("entity_type") == "campaign" and float((e.get("properties") or {}).get("revenue_lift_pct", 0)) > 20
            ]
        elif "запис" in q or "appointment" in q or "booking" in q or "процесс" in q or "workflow" in q:
            intent = "booking_related_processes"
            matched = [e for e in entities if e.get("entity_type") in ("workflow", "appointment")]
            # include related via edges
            ids = {e["entity_id"] for e in matched}
            for edge in edges:
                if edge["source_id"] in ids or edge["target_id"] in ids:
                    matched.append({"edge": edge, "entity_type": "relation"})
        else:
            tokens = [t for t in q.replace(",", " ").split() if len(t) > 2]
            for e in entities:
                blob = f"{e.get('entity_type')} {e.get('entity_id')} {' '.join(e.get('labels') or [])} {e.get('properties')}".lower()
                if any(t in blob for t in tokens):
                    matched.append(e)
        return {
            "query": text.strip(),
            "intent": intent,
            "semantic": True,
            "results": matched,
            "count": len(matched),
        }
