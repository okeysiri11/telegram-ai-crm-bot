"""AI Team Map & Live Organization — Sprint 29.2.

Visualizes the complete AI Organization in real time via Visual Event Bus.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.team_map.catalogs import (
    ACTIVITY_TYPES,
    AI_CARD_FIELDS,
    AI_CITY_APIS,
    EVENT_CHANNELS,
    LIVE_STATUSES,
    RELATIONSHIP_TYPES,
    VISUAL_OBJECT_FIELDS,
    WORKLOAD_METRICS,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _visual_id(object_type: str, logical_id: str) -> str:
    return f"viz_{object_type}_{logical_id}"


class VisualEventBus:
    """In-memory Visual Event Bus — subscribe, publish, poll for UI refresh."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def publish(self, channel: str, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        channel_norm = channel if channel in EVENT_CHANNELS else f"{channel} Events" if not channel.endswith("Events") else channel
        if channel_norm not in EVENT_CHANNELS:
            # allow short names
            mapping = {
                "ai": "AI Events",
                "workflow": "Workflow Events",
                "task": "Task Events",
                "knowledge": "Knowledge Events",
                "organization": "Organization Events",
                "registry": "Registry Events",
            }
            channel_norm = mapping.get(channel.lower().replace(" events", ""), channel)
        eid = _id("vevt")
        record = {
            "event_id": eid,
            "channel": channel_norm if channel_norm in EVENT_CHANNELS else channel,
            "event_type": event_type,
            "payload": payload or {},
            "published_at": _now(),
            "refresh_ui": True,
        }
        self.store.visual_events.save(eid, record)
        return record

    def subscribe(self, channels: list[str] | None = None) -> dict[str, Any]:
        wanted = set(channels or list(EVENT_CHANNELS))
        # normalize
        normalized = set()
        for c in wanted:
            if c in EVENT_CHANNELS:
                normalized.add(c)
            else:
                mapping = {
                    "ai": "AI Events",
                    "workflow": "Workflow Events",
                    "task": "Task Events",
                    "knowledge": "Knowledge Events",
                    "organization": "Organization Events",
                    "registry": "Registry Events",
                }
                normalized.add(mapping.get(c.lower(), c))
        sid = _id("vsub")
        record = {
            "subscription_id": sid,
            "channels": sorted(normalized),
            "created_at": _now(),
            "active": True,
        }
        self.store.visual_subscriptions.save(sid, record)
        return record

    def poll(self, since: str | None = None, limit: int = 50) -> dict[str, Any]:
        events = self.store.visual_events.list_all()
        events = sorted(events, key=lambda e: e.get("published_at") or "", reverse=True)
        if since:
            events = [e for e in events if (e.get("published_at") or "") > since]
        events = events[:limit]
        return {
            "count": len(events),
            "events": events,
            "channels": list(EVENT_CHANNELS),
            "auto_refresh_ui": True,
            "polled_at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "connected": True,
            "channels": list(EVENT_CHANNELS),
            "events": len(self.store.visual_events.list_all()),
            "subscriptions": len(self.store.visual_subscriptions.list_all()),
        }


class WorkloadEngine:
    def __init__(self) -> None:
        pass

    def for_card(self, status: str, index: int = 0) -> dict[str, Any]:
        load = {
            "Idle": 0.1,
            "Working": 0.72,
            "Thinking": 0.55,
            "Learning": 0.4,
            "Collaborating": 0.68,
            "Reviewing": 0.5,
            "Waiting": 0.25,
            "Offline": 0.0,
            "Completed": 0.15,
        }.get(status, 0.3)
        load = min(0.95, load + (index % 3) * 0.05)
        queue = int(load * 6)
        return {
            "Current Load": round(load, 2),
            "Task Queue": queue,
            "Response Time": f"{0.8 + load:.1f}s",
            "Availability": round(1.0 - load * 0.7, 2) if status != "Offline" else 0.0,
            "Utilization": round(load, 2),
            "Balanced Work Indicator": "balanced" if 0.3 <= load <= 0.75 else ("underutilized" if load < 0.3 else "overloaded"),
        }

    def overview(self, cards: list[dict[str, Any]]) -> dict[str, Any]:
        loads = [c.get("current_workload", {}).get("Current Load", 0) for c in cards]
        avg = sum(loads) / max(len(loads), 1)
        return {
            "metrics": list(WORKLOAD_METRICS),
            "average_load": round(avg, 2),
            "cards": [
                {
                    "logical_id": c["logical_id"],
                    "name": c["name"],
                    "workload": c.get("current_workload"),
                }
                for c in cards
            ],
            "balanced": 0.3 <= avg <= 0.75,
            "ready": True,
        }


class RelationshipEngine:
    def build(self, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        by_type: dict[str, list[dict[str, Any]]] = {}
        for n in nodes:
            by_type.setdefault(n["object_type"], []).append(n)

        edges: list[dict[str, Any]] = []

        def link(frm: dict[str, Any], to: dict[str, Any], relation: str, category: str) -> None:
            edges.append(
                {
                    "from": frm["logical_id"],
                    "to": to["logical_id"],
                    "from_visual": frm["visual_id"],
                    "to_visual": to["visual_id"],
                    "relation": relation,
                    "category": category,
                    "animated": True,
                }
            )

        owners = by_type.get("owner", [])
        concierges = by_type.get("concierge", [])
        departments = by_type.get("department", [])
        teams = by_type.get("ai_team", [])
        specialists = by_type.get("ai_specialist", [])

        for o in owners:
            for c in concierges:
                link(o, c, "orchestrates", "Organization Structure")
            for d in departments:
                link(o, d, "owns", "Organization Structure")

        for d in departments:
            for t in teams:
                if t.get("department") == d.get("name") or True:
                    link(d, t, "contains", "Department Links")
                    break

        for t in teams:
            for s in specialists:
                if s.get("department") == t.get("department") or True:
                    link(t, s, "member", "Organization Structure")
            for c in concierges:
                link(c, t, "coordinates", "AI Collaboration")

        for i, s in enumerate(specialists):
            if i + 1 < len(specialists):
                link(s, specialists[i + 1], "collaborates", "AI Collaboration")
            for c in concierges:
                link(s, c, "reports", "AI Collaboration")

        # Knowledge / workflow / task synthetic links
        if specialists and concierges:
            link(specialists[0], concierges[0], "knowledge_share", "Knowledge Flow")
        if teams and specialists:
            link(teams[0], specialists[0], "assigns_task", "Task Transfers")
        if departments and teams:
            link(departments[0], teams[0], "workflow", "Workflow Connections")

        grouped = {r: [e for e in edges if e["category"] == r] for r in RELATIONSHIP_TYPES}
        return {
            "edges": edges,
            "count": len(edges),
            "by_category": grouped,
            "relationship_types": list(RELATIONSHIP_TYPES),
            "ready": True,
        }


class AnimationLayer:
    def state_for(self, live_status: str) -> dict[str, Any]:
        anim = {
            "Idle": "breathe",
            "Working": "pulse",
            "Thinking": "orbit",
            "Learning": "ripple",
            "Collaborating": "link",
            "Reviewing": "scan",
            "Waiting": "wait_ring",
            "Offline": "dim",
            "Completed": "settle",
        }.get(live_status, "breathe")
        return {
            "animation": anim,
            "speed": 1.0 if live_status not in {"Offline", "Completed"} else 0.4,
            "glow": live_status in {"Working", "Thinking", "Collaborating", "Reviewing"},
            "connection_pulse": live_status in {"Collaborating", "Working"},
        }

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.2",
            "animations": ["breathe", "pulse", "orbit", "ripple", "link", "scan", "wait_ring", "dim", "settle"],
            "apis": list(AI_CITY_APIS),
        }

    def movement_api(self, logical_id: str, path: list[dict[str, float]] | None = None) -> dict[str, Any]:
        return {
            "api": "Movement API",
            "logical_id": logical_id,
            "path": path or [],
            "enabled": False,
            "planned": True,
            "note": "Movement reserved for AI City runtime",
        }

    def animation_api(self, logical_id: str, animation: str | None = None) -> dict[str, Any]:
        return {
            "api": "Animation API",
            "logical_id": logical_id,
            "animation": animation or "breathe",
            "ready": True,
        }

    def position_api(self, logical_id: str, x: float | None = None, y: float | None = None) -> dict[str, Any]:
        return {
            "api": "Position API",
            "logical_id": logical_id,
            "x": x,
            "y": y,
            "planned": x is None and y is None,
            "ready": True,
        }

    def visual_object_api(self, obj: dict[str, Any]) -> dict[str, Any]:
        return {
            "api": "Visual Object API",
            "object": obj,
            "fields": list(VISUAL_OBJECT_FIELDS),
            "ready": True,
        }


class LiveOrganizationMap:
    """Live Organization Map — real-time AI Team Map."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.event_bus = VisualEventBus(self.store)
        self.workload = WorkloadEngine()
        self.relationships = RelationshipEngine()
        self.animation = AnimationLayer()

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.2",
            "ai_team_map_ready": True,
            "live_organization_ready": True,
            "relationship_engine_ready": True,
            "visual_event_bus_connected": True,
            "animation_layer_ready": True,
            "workload_engine_ready": True,
            **full_catalog(),
            "event_bus": self.event_bus.status(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.2",
            "maps": len(self.store.org_maps.list_all()),
            "wizard_steps": len(WIZARD_STEPS),
            "event_bus": self.event_bus.status(),
        }

    def _seed_organization(self) -> list[dict[str, Any]]:
        """Build hierarchy nodes from registries + demo fallback."""
        nodes: list[dict[str, Any]] = []

        def add(
            logical_id: str,
            object_type: str,
            name: str,
            *,
            role: str = "",
            specialization: str = "",
            department: str = "",
            status: str = "Idle",
            task: str = "",
            knowledge_level: float = 0.7,
            health: str = "ok",
            x: float = 0,
            y: float = 0,
            avatar: str = "",
        ) -> dict[str, Any]:
            wl = self.workload.for_card(status, len(nodes))
            anim = self.animation.state_for(status)
            node = {
                "logical_id": logical_id,
                "visual_id": _visual_id(object_type, logical_id),
                "object_type": object_type,
                "name": name,
                "role": role or object_type.replace("_", " ").title(),
                "specialization": specialization,
                "department": department,
                "current_status": status,
                "current_task": task,
                "current_workload": wl,
                "knowledge_level": knowledge_level,
                "health": health,
                "avatar": avatar or f"avatar_{object_type}",
                "current_position": {"x": x, "y": y},
                "visual_state": {"live_status": status, "glow": anim["glow"]},
                "relationship_state": {"linked": True},
                "animation_state": anim,
                "lifecycle": "live",
            }
            nodes.append(node)
            return node

        # Prefer live registry data
        orgs = self.store.vertical_organizations.list_all()
        teams = self.store.collaborative_teams.list_all()
        ais = self.store.ai_registry.list_all()
        concierges = self.store.concierge_registry.list_all()

        add("owner_platform", "owner", "Platform Owner", role="Owner", status="Idle", x=400, y=40, avatar="avatar_owner")

        if concierges:
            c = concierges[0]
            add(
                c.get("concierge_id") or "concierge_live",
                "concierge",
                c.get("name") or "Organization Concierge",
                role="Orchestrator",
                specialization="Coordination",
                department="Leadership",
                status="Thinking",
                task="Coordinate AI organization",
                x=400,
                y=140,
            )
        else:
            add(
                "concierge_map",
                "concierge",
                "Organization Concierge",
                role="Orchestrator",
                specialization="Coordination",
                department="Leadership",
                status="Thinking",
                task="Coordinate AI organization",
                x=400,
                y=140,
            )

        dept_defs = [
            ("dept_ops", "Operations", 180, 260),
            ("dept_finance", "Finance", 400, 260),
            ("dept_legal", "Legal", 620, 260),
        ]
        for did, dname, x, y in dept_defs:
            add(did, "department", dname, role="Department", department=dname, status="Idle", x=x, y=y)

        if teams:
            for i, t in enumerate(teams[:3]):
                add(
                    t.get("team_id") or f"team_{i}",
                    "ai_team",
                    t.get("team_name") or f"AI Team {i+1}",
                    role="AI Team",
                    department=dept_defs[i % 3][1],
                    status="Collaborating",
                    task=t.get("business_goal") or "Team mission",
                    x=180 + i * 220,
                    y=380,
                )
        else:
            for i, (tid, tname, dept) in enumerate(
                (
                    ("team_ops", "Ops Collective", "Operations"),
                    ("team_fin", "Finance Collective", "Finance"),
                    ("team_legal", "Legal Collective", "Legal"),
                )
            ):
                add(tid, "ai_team", tname, role="AI Team", department=dept, status="Collaborating", task="Team mission", x=180 + i * 220, y=380)

        statuses_cycle = ["Working", "Analyzing", "Learning", "Reviewing", "Collaborating", "Waiting"]
        # Map Analyzing → Reviewing for 29.2 vocabulary if needed; use Reviewing
        statuses_cycle = ["Working", "Reviewing", "Learning", "Thinking", "Collaborating", "Waiting"]
        if ais:
            for i, a in enumerate(ais[:6]):
                st = statuses_cycle[i % len(statuses_cycle)]
                add(
                    a.get("agent_id") or f"ai_{i}",
                    "ai_specialist",
                    a.get("name") or f"Specialist {i+1}",
                    role="Specialist",
                    specialization=a.get("profession") or a.get("specialization") or "General",
                    department=dept_defs[i % 3][1],
                    status=st,
                    task=f"Active work item {i+1}",
                    knowledge_level=0.65 + (i % 3) * 0.1,
                    x=100 + i * 120,
                    y=520,
                )
        else:
            specs = [
                ("ai_legal", "Legal Specialist", "Lawyer", "Legal", "Reviewing"),
                ("ai_finance", "Finance Specialist", "Finance", "Finance", "Working"),
                ("ai_ops", "Ops Specialist", "Operations", "Operations", "Collaborating"),
                ("ai_marketing", "Marketing Specialist", "Marketing", "Operations", "Learning"),
                ("ai_hr", "HR Specialist", "HR", "Operations", "Thinking"),
                ("ai_analytics", "Analytics Specialist", "Analytics", "Finance", "Waiting"),
            ]
            for i, (aid, name, spec, dept, st) in enumerate(specs):
                add(
                    aid,
                    "ai_specialist",
                    name,
                    role="Specialist",
                    specialization=spec,
                    department=dept,
                    status=st,
                    task=f"Active work item {i+1}",
                    knowledge_level=0.7 + (i % 3) * 0.08,
                    x=100 + i * 120,
                    y=520,
                )

        if orgs:
            # already have owner; org label as department parent hint
            pass

        return nodes

    # Step 1 — Live Organization Map
    def map_view(self, *, department: str | None = None, search: str | None = None, status: str | None = None) -> dict[str, Any]:
        nodes = self._seed_organization()
        if department:
            d = department.lower()
            nodes = [
                n
                for n in nodes
                if n["object_type"] in {"owner", "concierge"}
                or (n.get("department") or "").lower() == d
                or n["object_type"] == "department"
                and n["name"].lower() == d
            ]
        if search:
            q = search.lower()
            nodes = [n for n in nodes if q in n["name"].lower() or q in (n.get("role") or "").lower() or q in n["logical_id"].lower()]
        if status:
            nodes = [n for n in nodes if n["current_status"].lower() == status.lower() or n["object_type"] in {"owner", "department", "concierge", "ai_team"}]

        rel = self.relationships.build(self._seed_organization())
        # filter edges to visible nodes
        ids = {n["logical_id"] for n in nodes}
        edges = [e for e in rel["edges"] if e["from"] in ids and e["to"] in ids]

        self.event_bus.publish("organization", "map_refreshed", {"node_count": len(nodes)})

        return {
            "title": "Live Organization Map",
            "nodes": nodes,
            "edges": edges,
            "hierarchy": {
                "owner": [n for n in nodes if n["object_type"] == "owner"],
                "concierge": [n for n in nodes if n["object_type"] == "concierge"],
                "departments": [n for n in nodes if n["object_type"] == "department"],
                "teams": [n for n in nodes if n["object_type"] == "ai_team"],
                "specialists": [n for n in nodes if n["object_type"] == "ai_specialist"],
            },
            "filters": {"department": department, "search": search, "status": status},
            "camera": {"zoom": 1.0, "pan": {"x": 0, "y": 0}},
            "ready": True,
        }

    # Step 2 — AI Cards
    def ai_cards(self, department: str | None = None) -> dict[str, Any]:
        nodes = [n for n in self._seed_organization() if n["object_type"] in {"ai_specialist", "concierge"}]
        if department:
            nodes = [n for n in nodes if (n.get("department") or "").lower() == department.lower()]
        cards = []
        for n in nodes:
            cards.append({k: n.get(k) for k in ("logical_id", "visual_id", *AI_CARD_FIELDS)})
            # flatten workload keys already in current_workload
        return {"cards": cards, "fields": list(AI_CARD_FIELDS), "count": len(cards), "ready": True}

    # Step 3 — Live Status
    def live_status(self) -> dict[str, Any]:
        nodes = self._seed_organization()
        counts = {s: 0 for s in LIVE_STATUSES}
        for n in nodes:
            if n["object_type"] in {"ai_specialist", "concierge", "ai_team"}:
                counts[n["current_status"]] = counts.get(n["current_status"], 0) + 1
        return {"statuses": list(LIVE_STATUSES), "counts": counts, "ready": True}

    # Step 4 — Workload Engine
    def workload_overview(self) -> dict[str, Any]:
        cards = self.ai_cards()["cards"]
        return self.workload.overview(cards)

    # Step 5 — Relationship Map
    def relationship_map(self) -> dict[str, Any]:
        return self.relationships.build(self._seed_organization())

    # Step 6 — Live Activity
    def live_activity(self) -> dict[str, Any]:
        nodes = self._seed_organization()
        specialists = [n for n in nodes if n["object_type"] == "ai_specialist"]
        channels = {
            "Current Conversations": [
                {"actor": n["name"], "detail": n["current_task"], "status": n["current_status"]}
                for n in specialists
                if n["current_status"] in {"Collaborating", "Thinking"}
            ],
            "Knowledge Updates": [
                {"actor": n["name"], "detail": f"Knowledge level {n['knowledge_level']}", "status": n["current_status"]}
                for n in specialists
                if n["current_status"] == "Learning"
            ],
            "Task Assignment": [
                {"actor": n["name"], "detail": n["current_task"], "status": n["current_status"]}
                for n in specialists
                if n["current_status"] in {"Working", "Waiting"}
            ],
            "Decision Making": [
                {"actor": n["name"], "detail": "Reviewing recommendation", "status": n["current_status"]}
                for n in specialists
                if n["current_status"] == "Reviewing"
            ],
            "Workflow Progress": [
                {"actor": n["name"], "detail": f"Utilization {n['current_workload']['Utilization']}", "status": n["current_status"]}
                for n in nodes
                if n["object_type"] == "ai_team"
            ],
        }
        self.event_bus.publish("task", "activity_snapshot", {"channels": list(channels.keys())})
        return {"channels": channels, "activity_types": list(ACTIVITY_TYPES), "ready": True}

    # Step 7 — Visual Event Bus
    def bus_subscribe(self, channels: list[str] | None = None) -> dict[str, Any]:
        sub = self.event_bus.subscribe(channels)
        # seed sample events for demo
        for ch, et in (
            ("AI Events", "status_changed"),
            ("Workflow Events", "step_advanced"),
            ("Task Events", "task_assigned"),
            ("Knowledge Events", "knowledge_shared"),
            ("Organization Events", "hierarchy_updated"),
            ("Registry Events", "registry_synced"),
        ):
            self.event_bus.publish(ch, et, {"source": "team_map"})
        return {**sub, "bus": self.event_bus.status()}

    def bus_poll(self, since: str | None = None) -> dict[str, Any]:
        return self.event_bus.poll(since=since)

    # Step 8 — Visual Objects
    def visual_objects(self, object_id: str | None = None) -> dict[str, Any]:
        nodes = self._seed_organization()
        objects = []
        for n in nodes:
            objects.append({k: n.get(k) for k in VISUAL_OBJECT_FIELDS} | {"name": n["name"], "object_type": n["object_type"]})
        if object_id:
            match = next((o for o in objects if o["logical_id"] == object_id or o["visual_id"] == object_id), None)
            if not match:
                raise NotFoundError(f"Visual object not found: {object_id}")
            return {"object": match, "fields": list(VISUAL_OBJECT_FIELDS)}
        return {"objects": objects, "count": len(objects), "fields": list(VISUAL_OBJECT_FIELDS)}

    # Step 9 — AI City foundation APIs
    def ai_city_apis(self, logical_id: str | None = None) -> dict[str, Any]:
        lid = logical_id or "ai_legal"
        nodes = self._seed_organization()
        node = next((n for n in nodes if n["logical_id"] == lid), nodes[-1] if nodes else {})
        vo = {k: node.get(k) for k in VISUAL_OBJECT_FIELDS}
        return {
            "apis": {
                "Movement API": self.animation.movement_api(lid),
                "Animation API": self.animation.animation_api(lid, (node.get("animation_state") or {}).get("animation")),
                "Position API": self.animation.position_api(
                    lid,
                    (node.get("current_position") or {}).get("x"),
                    (node.get("current_position") or {}).get("y"),
                ),
                "Visual Object API": self.animation.visual_object_api(vo),
            },
            "api_names": list(AI_CITY_APIS),
            "animation_layer": self.animation.catalog(),
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("tmap")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {"department": None, "search": "", "focus_status": None},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.team_map_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.team_map_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Team Map session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
        session["updated_at"] = _now()
        self.store.team_map_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        return {
            "session_id": session_id,
            "title": "Live Organization Map Summary",
            "map": self.map_view(department=draft.get("department"), search=draft.get("search")),
            "cards": self.ai_cards(draft.get("department")),
            "workload": self.workload_overview(),
            "relationships": self.relationship_map(),
            "activity": self.live_activity(),
            "event_bus": self.event_bus.status(),
            "ai_city": self.ai_city_apis(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        map_id = _id("omap")
        rel_id = _id("releng")
        wl_id = _id("wleng")
        anim_id = _id("anim")

        org_map = {
            "organization_map_id": map_id,
            "internal_id": map_id,
            "visual_id": _visual_id("organization_map", map_id),
            "object_type": "organization_map",
            "snapshot": self.map_view(),
            "registered_at": _now(),
            "sprint": "29.2",
        }
        rel_engine = {
            "relationship_engine_id": rel_id,
            "internal_id": rel_id,
            "visual_id": _visual_id("relationship_engine", rel_id),
            "snapshot": self.relationship_map(),
            "registered_at": _now(),
            "sprint": "29.2",
        }
        wl_engine = {
            "workload_engine_id": wl_id,
            "internal_id": wl_id,
            "visual_id": _visual_id("workload_engine", wl_id),
            "snapshot": self.workload_overview(),
            "registered_at": _now(),
            "sprint": "29.2",
        }
        anim_layer = {
            "animation_layer_id": anim_id,
            "internal_id": anim_id,
            "visual_id": _visual_id("animation_layer", anim_id),
            "catalog": self.animation.catalog(),
            "registered_at": _now(),
            "sprint": "29.2",
        }

        self.store.org_maps.save(map_id, org_map)
        self.store.relationship_engines.save(rel_id, rel_engine)
        self.store.workload_engines.save(wl_id, wl_engine)
        self.store.animation_layers.save(anim_id, anim_layer)

        self.event_bus.publish("registry", "map_registered", {"organization_map_id": map_id})

        session["status"] = "created"
        session["registrations"] = {
            "organization_map_id": map_id,
            "relationship_engine_id": rel_id,
            "workload_engine_id": wl_id,
            "animation_layer_id": anim_id,
        }
        session["updated_at"] = _now()
        self.store.team_map_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "organization_map": org_map,
            "relationship_engine": rel_engine,
            "workload_engine": wl_engine,
            "animation_layer": anim_layer,
            "event_bus": self.event_bus.status(),
            "message": "Organization Map, Relationship Engine, Workload Engine, and Animation Layer registered.",
        }
