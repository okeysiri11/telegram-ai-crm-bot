"""Platform Registry for Vertical Builder — Sprint 28.4."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.vertical.catalogs import VISUAL_CONSUMERS
from applications.platform_builder.vertical.visual_layer import make_dual_view


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class PlatformRegistry:
    """Registers vertical objects with Logical + Visual representations."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def _save_object(self, record: dict[str, Any]) -> dict[str, Any]:
        oid = record["object_id"]
        self.store.platform_registry.save(oid, record)
        return record

    def register_bundle(self, payload: dict[str, Any]) -> dict[str, Any]:
        vertical_id = payload.get("vertical_id") or _id("vertical")
        org_id = payload["organization_id"]
        brand = payload.get("brand_color_hex") or "#1B6CA8"
        city_slot = payload.get("city_position") or {"x": 12.0, "y": 8.0, "district": "enterprise_hub"}

        registered: list[dict[str, Any]] = []

        vertical = self._save_object(
            {
                **make_dual_view(
                    "vertical",
                    vertical_id,
                    payload["name"],
                    {
                        "icon": "vertical",
                        "color": brand,
                        "position": {"x": city_slot["x"], "y": city_slot["y"], "z": 0},
                        "city_slot": city_slot,
                        "industry": payload.get("industry"),
                        "description": payload.get("description"),
                    },
                ),
                "organization_id": org_id,
                "industry": payload.get("industry"),
                "modules": payload.get("modules") or [],
                "registry": "platform_builder_platform_registry",
                "lifecycle": "registered",
                "registered_at": _now(),
                "source": "vertical_builder",
                "sprint": "28.4",
            }
        )
        registered.append(vertical)

        module_ids = []
        for mid in payload.get("modules") or []:
            oid = _id(f"mod_{mid}")
            module_ids.append(oid)
            registered.append(
                self._save_object(
                    {
                        **make_dual_view(
                            "module",
                            oid,
                            mid,
                            {"icon": "module", "color": brand, "module_key": mid},
                        ),
                        "vertical_id": vertical_id,
                        "organization_id": org_id,
                        "module_key": mid,
                        "registered_at": _now(),
                        "source": "vertical_builder",
                    }
                )
            )

        workspace_id = _id("workspace")
        registered.append(
            self._save_object(
                {
                    **make_dual_view(
                        "workspace",
                        workspace_id,
                        payload.get("workspace_name") or f"{payload['name']} Workspace",
                        {
                            "icon": "workspace",
                            "color": brand,
                            "departments": payload.get("departments") or [],
                            "menus": payload.get("menus") or [],
                        },
                    ),
                    "vertical_id": vertical_id,
                    "organization_id": org_id,
                    "departments": payload.get("departments") or [],
                    "menus": payload.get("menus") or [],
                    "navigation": payload.get("navigation") or [],
                    "registered_at": _now(),
                    "source": "vertical_builder",
                }
            )
        )

        ai_refs = []
        for agent in payload.get("ai_team") or []:
            aid = agent.get("agent_id") or _id("ai_link")
            ai_refs.append(aid)
            registered.append(
                self._save_object(
                    {
                        **make_dual_view(
                            "ai_specialist",
                            aid,
                            agent.get("name") or "AI Specialist",
                            {
                                "icon": "ai",
                                "color": brand,
                                "profession": agent.get("profession"),
                            },
                        ),
                        "vertical_id": vertical_id,
                        "organization_id": org_id,
                        "linked_from": "ai_registry_or_seed",
                        "registered_at": _now(),
                        "source": "vertical_builder",
                    }
                )
            )

        concierge_id = None
        if payload.get("concierge"):
            c = payload["concierge"]
            concierge_id = c.get("concierge_id") or _id("concierge_link")
            registered.append(
                self._save_object(
                    {
                        **make_dual_view(
                            "concierge",
                            concierge_id,
                            c.get("name") or "Concierge",
                            {"icon": "concierge", "color": brand},
                        ),
                        "vertical_id": vertical_id,
                        "organization_id": org_id,
                        "not_an_ai_agent": True,
                        "registered_at": _now(),
                        "source": "vertical_builder",
                    }
                )
            )

        knowledge_id = _id("knowledge")
        registered.append(
            self._save_object(
                {
                    **make_dual_view(
                        "knowledge",
                        knowledge_id,
                        f"{payload['name']} Knowledge",
                        {"icon": "knowledge", "color": brand},
                    ),
                    "vertical_id": vertical_id,
                    "organization_id": org_id,
                    "topics": payload.get("knowledge_topics") or [],
                    "registered_at": _now(),
                    "source": "vertical_builder",
                }
            )
        )

        dashboard_id = _id("dashboard")
        registered.append(
            self._save_object(
                {
                    **make_dual_view(
                        "dashboard",
                        dashboard_id,
                        f"{payload['name']} Dashboard",
                        {
                            "icon": "dashboard",
                            "color": brand,
                            "widgets": payload.get("dashboard_widgets") or [],
                        },
                    ),
                    "vertical_id": vertical_id,
                    "organization_id": org_id,
                    "widgets": payload.get("dashboard_widgets") or [],
                    "registered_at": _now(),
                    "source": "vertical_builder",
                }
            )
        )

        organization = {
            "organization_id": org_id,
            "vertical_id": vertical_id,
            "name": payload.get("organization_name") or payload["name"],
            "industry": payload.get("industry"),
            "registered_at": _now(),
            "source": "vertical_builder",
            "sprint": "28.4",
        }
        self.store.vertical_organizations.save(org_id, organization)
        registered.append(
            self._save_object(
                {
                    **make_dual_view(
                        "organization",
                        org_id,
                        organization["name"],
                        {"icon": "organization", "color": brand, "city_slot": city_slot},
                    ),
                    "vertical_id": vertical_id,
                    "registered_at": _now(),
                    "source": "vertical_builder",
                }
            )
        )

        visual_layer = {
            "vertical_id": vertical_id,
            "organization_id": org_id,
            "objects": [
                {"object_id": r["object_id"], "kind": r["kind"], "visual": r["visual"], "logical": r["logical"]}
                for r in registered
            ],
            "prepared_for": list(VISUAL_CONSUMERS),
            "ready": True,
            "prepared_at": _now(),
        }
        self.store.visual_layers.save(vertical_id, visual_layer)

        bundle = {
            "vertical_id": vertical_id,
            "organization_id": org_id,
            "vertical": vertical,
            "module_ids": module_ids,
            "workspace_id": workspace_id,
            "ai_ids": ai_refs,
            "concierge_id": concierge_id,
            "knowledge_id": knowledge_id,
            "dashboard_id": dashboard_id,
            "organization": organization,
            "registered_objects": registered,
            "visual_layer": visual_layer,
            "platform_registry": "platform_builder_platform_registry",
            "count": len(registered),
        }
        self.store.vertical_registry.save(vertical_id, bundle)
        return bundle

    def list_all(self) -> dict[str, Any]:
        items = self.store.vertical_registry.list_all()
        return {
            "count": len(items),
            "items": items,
            "registry": "platform_builder_platform_registry",
            "object_count": len(self.store.platform_registry.list_all()),
        }

    def get(self, vertical_id: str) -> dict[str, Any] | None:
        return self.store.vertical_registry.get(vertical_id)
