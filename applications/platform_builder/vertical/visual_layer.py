"""Visual layer for Vertical Builder objects — Sprint 28.4."""

from __future__ import annotations

from typing import Any

from applications.platform_builder.vertical.catalogs import VISUAL_CONSUMERS


def make_dual_view(kind: str, object_id: str, label: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Every created object gets Logical + Visual representation."""
    meta = meta or {}
    return {
        "object_id": object_id,
        "kind": kind,
        "label": label,
        "logical": {
            "id": object_id,
            "type": kind,
            "name": label,
            "attributes": meta,
            "ready_for_ai_ops": True,
        },
        "visual": {
            "id": f"viz_{object_id}",
            "type": kind,
            "label": label,
            "icon": meta.get("icon") or kind,
            "color": meta.get("color") or "#1B6CA8",
            "position": meta.get("position") or {"x": 0, "y": 0, "z": 0},
            "city_slot": meta.get("city_slot"),
            "consumers": list(VISUAL_CONSUMERS),
            "ready_for_ai_city": True,
            "ready_for_3d": True,
        },
    }


def organization_map(
    *,
    owner: str,
    concierge: dict[str, Any] | None,
    departments: list[str],
    ai_team: list[dict[str, Any]],
    modules: list[str],
    brand_color: str,
    city_position: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Live Organization Preview compatible with future AI Operations Center."""
    pos = city_position or {"x": 12.0, "y": 8.0, "district": "enterprise_hub"}
    nodes = [
        {"id": "owner", "kind": "owner", "label": owner or "Owner", "visual": {"x": 0, "y": 0}},
    ]
    if concierge:
        nodes.append(
            {
                "id": concierge.get("concierge_id") or "concierge",
                "kind": "concierge",
                "label": concierge.get("name") or "Concierge",
                "visual": {"x": 0, "y": -2},
            }
        )
    for i, dept in enumerate(departments):
        nodes.append(
            {
                "id": f"dept_{i}",
                "kind": "department",
                "label": dept,
                "visual": {"x": -4 + i, "y": 2},
            }
        )
    for i, agent in enumerate(ai_team):
        nodes.append(
            {
                "id": agent.get("agent_id") or f"ai_{i}",
                "kind": "ai_specialist",
                "label": agent.get("name") or f"AI {i + 1}",
                "visual": {"x": 3 + (i % 3), "y": 1 + (i // 3)},
            }
        )
    connections = [
        {"from": "owner", "to": n["id"], "relation": "manages"}
        for n in nodes
        if n["id"] != "owner"
    ]
    return {
        "title": "Organization Map",
        "compatible_with": ["AI Operations Center", "AI Team Center", "2D AI City"],
        "owner": owner or "Owner",
        "concierge": concierge,
        "departments": departments,
        "ai_team": ai_team,
        "modules": modules,
        "brand_color": brand_color,
        "connections": connections,
        "nodes": nodes,
        "future_ai_city_position": pos,
        "visual_layer_ready": True,
    }
