"""AUTO 1.1 logistics operating desk — shipments, containers, ports, delay.

Mixin for AutoOpsService. Reuses AUTO 1.0 expenses, documents, photos, tasks, audit.
No live AIS / live container tracking. Manual values are labelled as such.
"""

from __future__ import annotations

import uuid
from typing import Any

from services.auto_ops.catalog import DOCUMENT_IDS, EXPENSE_IDS, PHOTO_IDS
from services.auto_ops.logistics_catalog import (
    CARRIER_TYPES,
    CONTAINER_STATUSES,
    CONTAINER_TYPES,
    DEFAULT_DELAY_THRESHOLDS,
    DEFAULT_LOGISTICS_POLICY,
    EVENT_TYPES,
    LOGISTICS_EXPENSE_IDS,
    LOGISTICS_TABS,
    REFERENCE_PORTS,
    SHIPMENT_STATUS_IDS,
    SHIPMENT_STATUS_LABELS,
    SHIPMENT_TYPE_IDS,
    SHIPMENT_TYPE_LABELS,
    TRUCK_TYPES,
    VESSEL_STATUSES,
    confirmation_for_source,
    delay_report,
    normalize_event_source,
    pipeline_for_status,
    suggested_task_title,
)
from services.auto_ops.rbac import AUTO_ROLES, can, normalize_role, require

CARRIER_TYPE_IDS = frozenset(dict(CARRIER_TYPES))
TRUCK_TYPE_IDS = frozenset(dict(TRUCK_TYPES))
CONTAINER_TYPE_IDS = frozenset(dict(CONTAINER_TYPES))
CONTAINER_STATUS_IDS = frozenset(dict(CONTAINER_STATUSES))
VESSEL_STATUS_IDS = frozenset(dict(VESSEL_STATUSES))
EVENT_TYPE_IDS = frozenset(dict(EVENT_TYPES))
EVENT_LABELS = dict(EVENT_TYPES)

LOGISTICS_BAG_KEYS = (
    "shipments",
    "carriers",
    "drivers",
    "trucks",
    "containers",
    "container_vehicles",
    "vessels",
    "ports",
    "logistics_events",
    "notifications",
    "logistics_settings",
    "logistics_providers",
)

SHIPMENT_FIELDS = (
    "vehicle_id",
    "shipment_type",
    "status",
    "origin_country",
    "origin_location",
    "destination_country",
    "destination_location",
    "pickup_address",
    "pickup_date_planned",
    "pickup_date_actual",
    "carrier_id",
    "driver_id",
    "truck_id",
    "container_id",
    "vessel_id",
    "booking_number",
    "bill_of_lading_number",
    "tracking_reference",
    "origin_port_id",
    "destination_port_id",
    "etd",
    "atd",
    "eta",
    "ata",
    "planned_eta",
    "current_eta",
    "customs_handoff_date",
    "delivery_date_planned",
    "delivery_date_actual",
    "responsible_manager_id",
    "assigned_forwarder_id",
    "accountant_reviewer_id",
    "customs_responsible_id",
    "shipment_number",
    "workspace_id",
    "current_location",
    "tracking_url",
    "provider_id",
    "client_id",
    "notes",
    "origin_lat",
    "origin_lng",
    "destination_lat",
    "destination_lng",
    "is_demo",
)

ACTIVE_SHIPMENT_STATUSES = SHIPMENT_STATUS_IDS - {"DELIVERED", "CANCELLED"}
CLOSED_CONTAINER = frozenset({"CLOSED", "UNLOADED"})

NOTIFY_DEDUPE_TYPES = frozenset(
    {
        "shipment_delayed",
        "eta_changed",
        "missing_document",
        "payment_overdue",
        "vehicle_reached_port",
        "container_assigned",
        "vessel_departed",
        "vessel_arrived",
        "delivery_completed",
    }
)

PORT_WORKFLOW = (
    ("arrival_at_port", "Прибытие в порт"),
    ("terminal", "Терминал"),
    ("container_loading", "Погрузка в контейнер"),
    ("export_release", "Экспортный выпуск"),
    ("vessel_loading", "Погрузка на судно"),
    ("departure", "Выход"),
    ("destination_arrival", "Прибытие в порт назначения"),
    ("port_release", "Выпуск из порта"),
)

STATUS_NOTIFY = {
    "ARRIVED_AT_PORT": "vehicle_reached_port",
    "ARRIVED_DESTINATION_PORT": "vessel_arrived",
    "LOADED_ON_VESSEL": "vessel_departed",
    "SEA_TRANSIT": "vessel_departed",
    "DELIVERED": "delivery_completed",
}


def _str(value: Any) -> str:
    return str(value or "").strip()


class AutoOpsLogisticsMixin:
    """Shipment / container / port desk. Expects AutoOpsService helpers."""

    def _thresholds(self, org: str) -> dict[str, int]:
        rows = self._bag(org).get("logistics_settings") or []
        raw = rows[0] if rows else {}
        yellow = int(raw.get("yellow_days") or DEFAULT_DELAY_THRESHOLDS["yellow_days"])
        orange = int(raw.get("orange_days") or DEFAULT_DELAY_THRESHOLDS["orange_days"])
        return {"yellow_days": yellow, "orange_days": orange}

    def _logistics_policy(self, org: str) -> dict[str, bool]:
        rows = self._bag(org).get("logistics_settings") or []
        raw = rows[0] if rows else {}
        out = dict(DEFAULT_LOGISTICS_POLICY)
        for key in DEFAULT_LOGISTICS_POLICY:
            if key in raw:
                out[key] = bool(raw.get(key))
        return out

    def _workspace_id(self, org: str, query: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> str:
        if body and body.get("workspace_id") not in (None, ""):
            return str(body["workspace_id"])
        if query and query.get("workspace_id") not in (None, ""):
            return str(query["workspace_id"])
        return org

    def _scoped_rows(self, org: str, items: list[dict[str, Any]], query: dict[str, str] | None = None) -> list[dict[str, Any]]:
        ws = self._workspace_id(org, query)
        out = []
        for row in items:
            if str(row.get("organization_id") or org) != org:
                continue
            if str(row.get("workspace_id") or org) != ws:
                continue
            out.append(row)
        return out

    def _real_actor(self, role: str | None, actor_id: str | None) -> str | None:
        if not actor_id:
            return None
        rid = normalize_role(role)
        raw = str(actor_id).strip()
        if raw.lower() in AUTO_ROLES or raw.lower() == rid:
            return None
        return raw

    def _shipment_assigned_to(self, org: str, ship: dict[str, Any], actor_id: str | None) -> bool:
        if not actor_id:
            return False
        aid = str(actor_id)
        if aid in {
            str(ship.get("responsible_manager_id") or ""),
            str(ship.get("assigned_forwarder_id") or ""),
            str(ship.get("customs_responsible_id") or ""),
        }:
            return True
        vehicle = self._find(org, "vehicles", str(ship.get("vehicle_id") or ""))
        return bool(vehicle and str(vehicle.get("assigned_manager_id") or "") == aid)

    def _next_shipment_number(self, org: str) -> str:
        n = len(self._bag(org)["shipments"]) + 1
        return f"SHP-{n:04d}"

    def _shipment_visible(self, org: str, ship: dict[str, Any], role: str | None, actor_id: str | None) -> bool:
        rid = normalize_role(role)
        actor = self._real_actor(role, actor_id)
        if rid not in {"auto_manager", "auto_forwarder"} or not actor:
            return True
        return self._shipment_assigned_to(org, ship, actor)

    def _require_manager_if_active(self, org: str, status: str, manager_id: Any) -> dict[str, Any] | None:
        policy = self._logistics_policy(org)
        if not policy.get("require_manager_on_active_shipment"):
            return None
        if str(status or "").upper() not in ACTIVE_SHIPMENT_STATUSES:
            return None
        if _str(manager_id):
            return None
        return {"ok": False, "error": "validation", "message_ru": "Для активной перевозки назначьте менеджера", "field": "responsible_manager_id"}

    def _shipment_delay(self, org: str, ship: dict[str, Any]) -> dict[str, Any]:
        th = self._thresholds(org)
        return delay_report(
            planned_eta=ship.get("planned_eta") or ship.get("eta") or ship.get("delivery_date_planned"),
            current_eta=ship.get("current_eta") or ship.get("eta"),
            delivery_date_planned=ship.get("delivery_date_planned"),
            status=str(ship.get("status") or ""),
            yellow_days=th["yellow_days"],
            orange_days=th["orange_days"],
        )

    def _name(self, org: str, key: str, item_id: Any, field: str = "name") -> str:
        if not item_id:
            return ""
        row = self._find(org, key, str(item_id))
        if not row:
            return ""
        return str(row.get(field) or row.get("company_name") or row.get("full_name") or row.get("container_number") or "")

    def _port_name(self, org: str, port_id: Any) -> str:
        if not port_id:
            return ""
        pid = str(port_id)
        row = self._find(org, "ports", pid)
        if row:
            return str(row.get("name") or row.get("unlocode") or "")
        for ref in REFERENCE_PORTS:
            if ref["unlocode"] == pid or ref["name"] == pid:
                return ref["name"]
        return pid

    def _active_container_for_vehicle(self, org: str, vehicle_id: str) -> dict[str, Any] | None:
        for link in self._bag(org)["container_vehicles"]:
            if str(link.get("vehicle_id")) != str(vehicle_id):
                continue
            if link.get("released_at"):
                continue
            container = self._find(org, "containers", str(link.get("container_id") or ""))
            if not container:
                continue
            if str(container.get("status") or "").upper() in CLOSED_CONTAINER:
                continue
            return container
        return None

    def _container_vehicles(self, org: str, container_id: str, *, active_only: bool = False) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for link in self._bag(org)["container_vehicles"]:
            if str(link.get("container_id")) != str(container_id):
                continue
            if active_only and link.get("released_at"):
                continue
            vehicle = self._find(org, "vehicles", str(link.get("vehicle_id") or ""))
            out.append({**link, "vehicle": self._public_vehicle(org, vehicle) if vehicle else None})
        return out

    def _logistics_costs(self, org: str, *, vehicle_id: str | None = None, shipment_id: str | None = None) -> dict[str, Any]:
        planned = actual = paid = unpaid = 0.0
        lines: list[dict[str, Any]] = []
        for exp in self._bag(org)["expenses"]:
            if str(exp.get("payment_status") or "") == "cancelled":
                continue
            if shipment_id and str(exp.get("shipment_id") or "") != str(shipment_id):
                continue
            if vehicle_id and str(exp.get("vehicle_id") or "") != str(vehicle_id):
                continue
            if not shipment_id and not vehicle_id:
                continue
            cat = str(exp.get("category") or "OTHER")
            if cat not in LOGISTICS_EXPENSE_IDS and cat not in {"INLAND_TRANSPORT", "SEA_FREIGHT", "PORT_FEE", "STORAGE", "BROKER"}:
                continue
            base = self._expense_base(exp)
            status = str(exp.get("payment_status") or "paid")
            if status == "planned":
                planned += base
            else:
                actual += base
                if status == "paid":
                    paid += base
                else:
                    unpaid += base
            lines.append(exp)
        return {
            "planned": round(planned, 2),
            "actual": round(actual, 2),
            "paid": round(paid, 2),
            "unpaid": round(unpaid, 2),
            "difference": round(actual - planned, 2),
            "currency": "USD",
            "from_records": True,
            "lines": lines,
        }

    def _public_shipment(self, org: str, ship: dict[str, Any], role: str | None = None, actor_id: str | None = None) -> dict[str, Any]:
        vehicle = self._find(org, "vehicles", str(ship.get("vehicle_id") or ""))
        delay = self._shipment_delay(org, ship)
        status = str(ship.get("status") or "")
        stype = str(ship.get("shipment_type") or "")
        current_location = ship.get("current_location") or (
            ship.get("origin_location")
            if status in {"PLANNED", "BOOKED", "AWAITING_PICKUP"}
            else ship.get("destination_location")
            if status in {"DELIVERED"}
            else self._port_name(org, ship.get("destination_port_id"))
            if status in {"ARRIVED_DESTINATION_PORT", "PORT_RELEASE", "CUSTOMS_HANDOFF"}
            else self._name(org, "vessels", ship.get("vessel_id"))
            if status in {"LOADED_ON_VESSEL", "SEA_TRANSIT"}
            else self._name(org, "containers", ship.get("container_id"), "container_number")
            if status in {"LOADED_IN_CONTAINER"}
            else self._port_name(org, ship.get("origin_port_id"))
            if status in {"ARRIVED_AT_PORT", "PORT_PROCESSING"}
            else ship.get("origin_location")
            or (vehicle or {}).get("location_current")
        )
        cover = self._cover_file(org, vehicle) if vehicle else None
        finance_ok = can(role, "finance") if role is not None else True
        actor = self._real_actor(role, actor_id)
        policy = self._logistics_policy(org)
        show_ops_cost = finance_ok or (
            policy.get("manager_see_assigned_transport_cost")
            and normalize_role(role) in {"auto_manager", "auto_forwarder"}
            and self._shipment_assigned_to(org, ship, actor)
        )
        costs = self._logistics_costs(org, shipment_id=str(ship.get("id")), vehicle_id=str(ship.get("vehicle_id") or "")) if show_ops_cost else {"restricted": True}
        if show_ops_cost and not finance_ok:
            costs = {k: costs[k] for k in ("planned", "actual", "paid", "unpaid", "currency", "from_records") if k in costs}
            costs["operational_only"] = True
            costs["profit"] = None
        origin = ship.get("origin_location") or self._port_name(org, ship.get("origin_port_id")) or ship.get("origin_country")
        dest = ship.get("destination_location") or self._port_name(org, ship.get("destination_port_id")) or ship.get("destination_country")
        has_coords = all(ship.get(k) not in (None, "") for k in ("origin_lat", "origin_lng", "destination_lat", "destination_lng"))
        client_id = ship.get("client_id") or (vehicle or {}).get("client_id")
        client_name = self._client_name(org, str(client_id) if client_id else None)
        tracking_url = ship.get("tracking_url")
        return {
            **ship,
            "status_ru": SHIPMENT_STATUS_LABELS.get(status, status),
            "shipment_type_ru": SHIPMENT_TYPE_LABELS.get(stype, stype),
            "vehicle_title": self._vehicle_title(vehicle) if vehicle else "",
            "vin": (vehicle or {}).get("vin"),
            "client_id": client_id,
            "client_name": client_name,
            "cover_file_id": cover,
            "carrier_name": self._name(org, "carriers", ship.get("carrier_id"), "company_name"),
            "container_number": self._name(org, "containers", ship.get("container_id"), "container_number"),
            "vessel_name": self._name(org, "vessels", ship.get("vessel_id")),
            "origin_port_name": self._port_name(org, ship.get("origin_port_id")),
            "destination_port_name": self._port_name(org, ship.get("destination_port_id")),
            "current_location": current_location or "—",
            "delay": delay,
            "pipeline": pipeline_for_status(status),
            "costs": costs,
            "eta_source_label_ru": "Введено вручную",
            "tracking_mode": "manual",
            "tracking_url": tracking_url,
            "tracking_unavailable_ru": "Автоматическое отслеживание недоступно",
            "route": {
                "label_ru": "Схема маршрута, не live-tracking",
                "origin": origin,
                "port": self._port_name(org, ship.get("origin_port_id")) or self._port_name(org, ship.get("destination_port_id")),
                "destination": dest,
                "has_coordinates": has_coords,
                "points": [
                    {"kind": "origin", "label": origin, "lat": ship.get("origin_lat"), "lng": ship.get("origin_lng")},
                    {"kind": "origin_port", "label": self._port_name(org, ship.get("origin_port_id")) or None},
                    {"kind": "destination_port", "label": self._port_name(org, ship.get("destination_port_id")) or None},
                    {"kind": "destination", "label": dest, "lat": ship.get("destination_lat"), "lng": ship.get("destination_lng")},
                ],
            },
            "port_workflow": [{"id": i, "label_ru": l} for i, l in PORT_WORKFLOW],
        }

    def vehicle_logistics_block(self, org: str, vehicle_id: str, role: str | None) -> dict[str, Any]:
        shipments = [s for s in self._bag(org)["shipments"] if str(s.get("vehicle_id")) == str(vehicle_id)]
        shipments.sort(key=lambda s: str(s.get("updated_at") or ""), reverse=True)
        current = next((s for s in shipments if str(s.get("status")) in ACTIVE_SHIPMENT_STATUSES), shipments[0] if shipments else None)
        if not current:
            return {"shipment": None, "shipments": [], "message_ru": "Перевозка ещё не создана."}
        pub = self._public_shipment(org, current, role)
        events = [e for e in self._bag(org)["logistics_events"] if str(e.get("shipment_id")) == str(current.get("id"))]
        docs = [
            d
            for d in self._bag(org)["documents"]
            if not d.get("archived_at")
            and (
                str(d.get("shipment_id") or "") == str(current.get("id"))
                or str(d.get("vehicle_id") or "") == str(vehicle_id)
                or str(d.get("container_id") or "") == str(current.get("container_id") or "")
            )
        ]
        photos = [
            p
            for p in self._bag(org)["photos"]
            if str(p.get("shipment_id") or "") == str(current.get("id")) or str(p.get("vehicle_id") or "") == str(vehicle_id)
        ]
        return {
            "shipment": pub,
            "shipments": [self._public_shipment(org, s, role) for s in shipments],
            "events": events,
            "documents": docs,
            "photos": photos,
            "container": self._find(org, "containers", str(current.get("container_id") or "")),
            "vessel": self._find(org, "vessels", str(current.get("vessel_id") or "")),
            "carrier": self._find(org, "carriers", str(current.get("carrier_id") or "")),
            "history": self._vehicle_history_rows(org, vehicle_id),
        }

    def _vehicle_history_rows(self, org: str, vehicle_id: str) -> list[dict[str, Any]]:
        shipments = [s for s in self._bag(org)["shipments"] if str(s.get("vehicle_id")) == str(vehicle_id)]
        ship_ids = {str(s.get("id")) for s in shipments}
        items: list[dict[str, Any]] = []
        for ev in self._bag(org)["logistics_events"]:
            if str(ev.get("shipment_id") or "") not in ship_ids:
                continue
            src = normalize_event_source(ev.get("source"))
            items.append(
                {
                    "kind": "event",
                    "id": ev.get("id"),
                    "at": ev.get("created_at"),
                    "title": ev.get("description") or ev.get("event_type"),
                    "event_type": ev.get("event_type"),
                    "source": src,
                    "confirmation": ev.get("confirmation") or confirmation_for_source(src),
                    "location": ev.get("location"),
                    "shipment_id": ev.get("shipment_id"),
                }
            )
        for a in self._bag(org)["audit"]:
            eid = str(a.get("entity_id") or "")
            nv = a.get("new_value") or {}
            if eid not in ship_ids and eid != str(vehicle_id) and str(nv.get("vehicle_id") or "") != str(vehicle_id):
                continue
            items.append(
                {
                    "kind": "audit",
                    "id": a.get("id"),
                    "at": a.get("created_at"),
                    "title": a.get("summary") or a.get("action"),
                    "action": a.get("action"),
                    "source": "SYSTEM",
                    "confirmation": "CONFIRMED",
                    "shipment_id": eid if eid in ship_ids else None,
                }
            )
        items.sort(key=lambda r: str(r.get("at") or ""))
        return items

    async def _add_event(
        self,
        org: str,
        *,
        shipment_id: str,
        event_type: str,
        description: str,
        role: str | None,
        actor_id: str | None,
        location: str | None = None,
        document_id: str | None = None,
        photo_id: str | None = None,
        source: str = "manual",
        confirmation: str | None = None,
    ) -> dict[str, Any]:
        et = event_type if event_type in EVENT_TYPE_IDS else "comment"
        src = normalize_event_source(source)
        conf = confirmation_for_source(src, confirmation)
        ship = self._find(org, "shipments", shipment_id) or {}
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": ship.get("workspace_id") or org,
            "shipment_id": shipment_id,
            "event_type": et,
            "description": description,
            "actor_id": actor_id or normalize_role(role),
            "actor_role": normalize_role(role),
            "source": src,
            "confirmation": conf,
            "location": location,
            "document_id": document_id,
            "photo_id": photo_id,
            "created_at": self._now(),
            "updated_at": self._now(),
            "immutable": True,
        }
        saved = await self._persist("logistics_event", item)
        self._bag(org)["logistics_events"].insert(0, saved)
        return saved

    async def _notify(
        self,
        org: str,
        *,
        ntype: str,
        title: str,
        entity_type: str,
        entity_id: str,
        shipment_id: str | None = None,
        vehicle_id: str | None = None,
    ) -> dict[str, Any] | None:
        if ntype not in NOTIFY_DEDUPE_TYPES:
            ntype = "other"
        day = str(self._now())[:10]
        key = f"{ntype}:{entity_type}:{entity_id}:{day}"
        for existing in self._bag(org)["notifications"]:
            if existing.get("dedupe_key") == key:
                return None
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "notification_type": ntype,
            "title": title,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "shipment_id": shipment_id,
            "vehicle_id": vehicle_id,
            "dedupe_key": key,
            "channel": "desk",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        saved = await self._persist("notification", item)
        self._bag(org)["notifications"].insert(0, saved)
        return saved

    async def list_shipments(self, organization_id: str, role: str | None, query: dict[str, str] | None = None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        q = query or {}
        rows = [s for s in self._scoped_rows(org, self._bag(org)["shipments"], q) if self._shipment_visible(org, s, role, actor_id)]
        items = [self._public_shipment(org, s, role, actor_id) for s in rows]
        tab = (q.get("tab") or "all").strip()
        tab_def = next((t for t in LOGISTICS_TABS if t["id"] == tab), LOGISTICS_TABS[0])
        if tab_def.get("problems"):
            wanted = set(tab_def.get("statuses") or [])
            items = [
                s
                for s in items
                if str(s.get("status")) in wanted
                or (s.get("delay") or {}).get("level") in {"orange", "red"}
                or (s.get("delay") or {}).get("overdue")
            ]
        elif tab_def.get("statuses"):
            wanted = set(tab_def["statuses"])
            items = [s for s in items if str(s.get("status")) in wanted]
        elif tab_def.get("exclude"):
            excl = set(tab_def["exclude"])
            items = [s for s in items if str(s.get("status")) not in excl]
        status = (q.get("status") or "").strip().upper()
        country = (q.get("country") or "").strip().lower()
        port = (q.get("port") or "").strip().lower()
        carrier = (q.get("carrier") or q.get("carrier_id") or "").strip()
        manager = (q.get("manager") or q.get("responsible_manager_id") or "").strip()
        delayed_only = (q.get("delayed") or q.get("delayed_only") or "").lower() in {"1", "true", "yes"}
        eta_from = (q.get("eta_from") or "").strip()
        eta_to = (q.get("eta_to") or "").strip()
        search = (q.get("q") or q.get("search") or "").strip().upper()
        if status:
            items = [s for s in items if str(s.get("status")) == status]
        if country:
            items = [
                s
                for s in items
                if country in str(s.get("origin_country") or "").lower() or country in str(s.get("destination_country") or "").lower()
            ]
        if port:
            items = [
                s
                for s in items
                if port in str(s.get("origin_port_id") or "").lower()
                or port in str(s.get("destination_port_id") or "").lower()
                or port in str(s.get("origin_port_name") or "").lower()
                or port in str(s.get("destination_port_name") or "").lower()
            ]
        if carrier:
            items = [s for s in items if str(s.get("carrier_id") or "") == carrier or carrier.lower() in str(s.get("carrier_name") or "").lower()]
        if manager:
            items = [s for s in items if str(s.get("responsible_manager_id") or "") == manager]
        if delayed_only:
            items = [s for s in items if int((s.get("delay") or {}).get("delay_days") or 0) > 0 or (s.get("delay") or {}).get("overdue")]
        if eta_from:
            items = [s for s in items if str((s.get("delay") or {}).get("current_eta") or s.get("eta") or "") >= eta_from]
        if eta_to:
            items = [s for s in items if str((s.get("delay") or {}).get("current_eta") or s.get("eta") or "") <= eta_to]
        if search:

            def hay(s: dict[str, Any]) -> str:
                return " ".join(
                    str(s.get(k) or "")
                    for k in (
                        "vin",
                        "vehicle_title",
                        "container_number",
                        "booking_number",
                        "bill_of_lading_number",
                        "vessel_name",
                        "carrier_name",
                        "tracking_reference",
                        "shipment_number",
                        "client_name",
                    )
                ).upper()

            items = [s for s in items if search in hay(s)]
        counts = {t["id"]: 0 for t in LOGISTICS_TABS}
        all_pub = [self._public_shipment(org, s, role, actor_id) for s in rows]
        for t in LOGISTICS_TABS:
            if t.get("problems"):
                wanted = set(t.get("statuses") or [])
                counts[t["id"]] = sum(
                    1
                    for s in all_pub
                    if str(s.get("status")) in wanted or (s.get("delay") or {}).get("level") in {"orange", "red"} or (s.get("delay") or {}).get("overdue")
                )
            elif t.get("statuses"):
                wanted = set(t["statuses"])
                counts[t["id"]] = sum(1 for s in all_pub if str(s.get("status")) in wanted)
            else:
                excl = set(t.get("exclude") or [])
                counts[t["id"]] = sum(1 for s in all_pub if str(s.get("status")) not in excl)
        return {"ok": True, "items": items, "total": len(items), "tabs": LOGISTICS_TABS, "counts": counts}

    async def get_shipment(self, organization_id: str, shipment_id: str, role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        ship = self._find(org, "shipments", shipment_id)
        if not ship:
            return {"ok": False, "error": "not_found", "message_ru": "Перевозка не найдена"}
        if not self._shipment_visible(org, ship, role, actor_id):
            return {"ok": False, "error": "forbidden", "message_ru": "Перевозка недоступна для вашей роли"}
        events = [e for e in self._bag(org)["logistics_events"] if str(e.get("shipment_id")) == str(shipment_id)]
        docs = [d for d in self._bag(org)["documents"] if not d.get("archived_at") and str(d.get("shipment_id") or "") == str(shipment_id)]
        photos = [p for p in self._bag(org)["photos"] if str(p.get("shipment_id") or "") == str(shipment_id)]
        tasks = [t for t in self._bag(org)["tasks"] if str(t.get("shipment_id") or "") == str(shipment_id)]
        return {
            "ok": True,
            "item": self._public_shipment(org, ship, role, actor_id),
            "events": events,
            "documents": docs,
            "photos": photos,
            "tasks": tasks,
            "notifications": [n for n in self._bag(org)["notifications"] if str(n.get("shipment_id") or "") == str(shipment_id)][:20],
        }

    def _write_denied(self, role: str | None) -> dict[str, Any] | None:
        if can(role, "create") or can(role, "edit"):
            return None
        return require(role, "edit")

    async def create_shipment(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicle_id = _str(body.get("vehicle_id"))
        if not vehicle_id or not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "validation", "message_ru": "Перевозка должна быть привязана к существующему автомобилю"}
        stype = _str(body.get("shipment_type") or "CONTAINER").upper()
        if stype not in SHIPMENT_TYPE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип перевозки", "field": "shipment_type"}
        status = _str(body.get("status") or "PLANNED").upper()
        if status not in SHIPMENT_STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус перевозки", "field": "status"}
        manager_id = body.get("responsible_manager_id")
        blocked = self._require_manager_if_active(org, status, manager_id)
        if blocked:
            return blocked
        item: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": self._workspace_id(org, body=body),
            "vehicle_id": vehicle_id,
            "shipment_type": stype,
            "status": status,
            "shipment_number": _str(body.get("shipment_number")) or self._next_shipment_number(org),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": actor_id or normalize_role(role),
            "is_demo": bool(body.get("is_demo")),
            "eta_source": "manual",
        }
        for field in SHIPMENT_FIELDS:
            if field in {"vehicle_id", "shipment_type", "status", "is_demo"}:
                continue
            if field in body and body[field] not in (None, ""):
                item[field] = body[field]
        if item.get("eta") and not item.get("current_eta"):
            item["current_eta"] = item["eta"]
        if item.get("eta") and not item.get("planned_eta"):
            item["planned_eta"] = item["eta"]
        saved = await self._persist("shipment", item)
        self._bag(org)["shipments"].insert(0, saved)
        await self._audit(
            organization_id=org,
            action="shipment_created",
            entity_type="shipment",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            new_value={"vehicle_id": vehicle_id, "status": status, "shipment_type": stype},
            summary=f"Создана перевозка {stype}",
        )
        await self._audit(
            organization_id=org,
            action="vehicle_linked",
            entity_type="shipment",
            entity_id=str(saved["id"]),
            role=role,
            actor_id=actor_id,
            new_value={"vehicle_id": vehicle_id},
            summary="Автомобиль привязан к перевозке",
        )
        await self._add_event(org, shipment_id=str(saved["id"]), event_type="status_changed", description="Перевозка создана", role=role, actor_id=actor_id, source="system")
        return {"ok": True, "item": self._public_shipment(org, saved, role, actor_id)}

    async def update_shipment(self, organization_id: str, shipment_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        if "status" in body and normalize_role(role) == "auto_accountant" and not self._logistics_policy(org).get("accountant_may_change_status"):
            return {"ok": False, "error": "forbidden", "message_ru": "Бухгалтер не меняет операционный статус перевозки"}
        denied = self._write_denied(role)
        if denied:
            return denied
        item = self._find(org, "shipments", shipment_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Перевозка не найдена"}
        old = {k: item.get(k) for k in ("status", "carrier_id", "container_id", "vessel_id", "eta", "current_eta", "driver_id", "vehicle_id", "current_location")}
        patch: dict[str, Any] = {}
        if "status" in body:
            status = _str(body.get("status")).upper()
            if status not in SHIPMENT_STATUS_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус", "field": "status"}
            patch["status"] = status
        if "shipment_type" in body:
            stype = _str(body.get("shipment_type")).upper()
            if stype not in SHIPMENT_TYPE_IDS:
                return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип", "field": "shipment_type"}
            patch["shipment_type"] = stype
        for field in SHIPMENT_FIELDS:
            if field in {"status", "shipment_type"}:
                continue
            if field in body:
                patch[field] = body[field]
        if "eta" in patch and "current_eta" not in body:
            patch["current_eta"] = patch["eta"]
        next_status = str(patch.get("status") or item.get("status") or "")
        next_manager = patch.get("responsible_manager_id", item.get("responsible_manager_id"))
        blocked = self._require_manager_if_active(org, next_status, next_manager)
        if blocked:
            return blocked
        patch["updated_at"] = self._now()
        patch["updated_by"] = actor_id or normalize_role(role)
        item.update(patch)
        await self._persist_update("shipment", shipment_id, patch)
        action = "shipment_updated"
        suggested: list[dict[str, Any]] = []
        if old.get("status") != item.get("status"):
            action = "status_changed"
            await self._add_event(
                org,
                shipment_id=shipment_id,
                event_type="status_changed",
                description=f"Этап: {SHIPMENT_STATUS_LABELS.get(str(item.get('status')), item.get('status'))}",
                role=role,
                actor_id=actor_id,
                source="manual",
            )
            ntype = STATUS_NOTIFY.get(str(item.get("status")))
            if ntype:
                await self._notify(
                    org,
                    ntype=ntype,
                    title=str(SHIPMENT_STATUS_LABELS.get(str(item.get("status")), item.get("status"))),
                    entity_type="shipment",
                    entity_id=shipment_id,
                    shipment_id=shipment_id,
                    vehicle_id=str(item.get("vehicle_id") or ""),
                )
            if str(item.get("status")) == "DELIVERED":
                action = "delivery_completed"
            suggested = await self._apply_suggested_tasks(org, item, role, actor_id)
        if old.get("carrier_id") != item.get("carrier_id"):
            action = "carrier_changed"
            await self._add_event(org, shipment_id=shipment_id, event_type="carrier_assigned", description="Назначен перевозчик", role=role, actor_id=actor_id)
        if old.get("container_id") != item.get("container_id"):
            action = "container_changed" if old.get("container_id") else "container_assigned"
            await self._add_event(org, shipment_id=shipment_id, event_type="container_assigned", description="Назначен контейнер", role=role, actor_id=actor_id)
            await self._notify(org, ntype="container_assigned", title="Назначен контейнер", entity_type="shipment", entity_id=shipment_id, shipment_id=shipment_id, vehicle_id=str(item.get("vehicle_id") or ""))
            cid = str(item.get("container_id") or "")
            vid = str(item.get("vehicle_id") or "")
            if cid and vid:
                existing = self._active_container_for_vehicle(org, vid)
                if existing and str(existing.get("id")) != cid:
                    for link in self._bag(org)["container_vehicles"]:
                        if str(link.get("vehicle_id")) == vid and not link.get("released_at"):
                            link["released_at"] = self._now()
                already = next((l for l in self._bag(org)["container_vehicles"] if str(l.get("container_id")) == cid and str(l.get("vehicle_id")) == vid and not l.get("released_at")), None)
                if not already:
                    link_item = {
                        "id": str(uuid.uuid4()),
                        "organization_id": org,
                        "tenant_id": org,
                        "container_id": cid,
                        "vehicle_id": vid,
                        "released_at": None,
                        "created_at": self._now(),
                        "updated_at": self._now(),
                    }
                    saved_link = await self._persist("container_vehicle", link_item)
                    self._bag(org)["container_vehicles"].insert(0, saved_link)
        if old.get("vessel_id") != item.get("vessel_id"):
            action = "vessel_changed"
            await self._add_event(org, shipment_id=shipment_id, event_type="vessel_assigned", description="Назначено судно", role=role, actor_id=actor_id)
        if old.get("driver_id") != item.get("driver_id"):
            action = "driver_assignment"
        if old.get("eta") != item.get("eta") or old.get("current_eta") != item.get("current_eta"):
            action = "eta_changed"
            await self._add_event(org, shipment_id=shipment_id, event_type="eta_changed", description="ETA изменена (введено вручную)", role=role, actor_id=actor_id)
            await self._notify(org, ntype="eta_changed", title="ETA изменена", entity_type="shipment", entity_id=shipment_id, shipment_id=shipment_id, vehicle_id=str(item.get("vehicle_id") or ""))
        if old.get("vehicle_id") != item.get("vehicle_id") and item.get("vehicle_id"):
            action = "vehicle_linked"
            await self._audit(
                organization_id=org,
                action="vehicle_linked",
                entity_type="shipment",
                entity_id=shipment_id,
                role=role,
                actor_id=actor_id,
                new_value={"vehicle_id": item.get("vehicle_id")},
                summary="Автомобиль привязан к перевозке",
            )
        if old.get("current_location") != item.get("current_location") and item.get("current_location") not in (None, ""):
            action = "location_updated"
            await self._add_event(
                org,
                shipment_id=shipment_id,
                event_type="location_updated",
                description=f"Местоположение: {item.get('current_location')}",
                role=role,
                actor_id=actor_id,
                location=str(item.get("current_location")),
                source="manual",
                confirmation="CONFIRMED",
            )
            await self._audit(
                organization_id=org,
                action="location_updated",
                entity_type="shipment",
                entity_id=shipment_id,
                role=role,
                actor_id=actor_id,
                old_value={"current_location": old.get("current_location")},
                new_value={"current_location": item.get("current_location")},
                summary="Ручное обновление местоположения",
            )
        delay = self._shipment_delay(org, item)
        if delay.get("overdue") or delay.get("level") in {"orange", "red"}:
            await self._notify(org, ntype="shipment_delayed", title="Задержка перевозки", entity_type="shipment", entity_id=shipment_id, shipment_id=shipment_id, vehicle_id=str(item.get("vehicle_id") or ""))
        await self._audit(
            organization_id=org,
            action=action,
            entity_type="shipment",
            entity_id=shipment_id,
            role=role,
            actor_id=actor_id,
            old_value=old,
            new_value={k: item.get(k) for k in old},
            summary=action,
        )
        return {"ok": True, "item": self._public_shipment(org, item, role, actor_id), "suggested_tasks": suggested}

    async def _apply_suggested_tasks(self, org: str, ship: dict[str, Any], role: str | None, actor_id: str | None) -> list[dict[str, Any]]:
        title = suggested_task_title(str(ship.get("status") or ""))
        if not title:
            return []
        suggestion = {
            "title": title,
            "status": str(ship.get("status")),
            "suggested": True,
            "source": "SYSTEM",
            "irreversible": False,
        }
        if not self._logistics_policy(org).get("auto_create_suggested_tasks"):
            return [suggestion]
        sid = str(ship.get("id"))
        existing = next(
            (
                t
                for t in self._bag(org)["tasks"]
                if str(t.get("shipment_id") or "") == sid and str(t.get("title") or "") == title and t.get("status") in {"open", "in_progress"}
            ),
            None,
        )
        if existing:
            return [{**suggestion, "id": existing.get("id"), "created": False}]
        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": ship.get("workspace_id") or org,
            "title": title,
            "status": "open",
            "priority": "normal",
            "vehicle_id": ship.get("vehicle_id"),
            "shipment_id": sid,
            "suggested": True,
            "source": "SYSTEM",
            "assigned_manager_id": ship.get("responsible_manager_id"),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        saved = await self._persist("task", item)
        self._bag(org)["tasks"].insert(0, saved)
        await self._add_event(org, shipment_id=sid, event_type="task_created", description=title, role=role, actor_id=actor_id, source="system")
        return [{**suggestion, "id": saved["id"], "created": True}]

    async def add_shipment_event(self, organization_id: str, shipment_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        ship = self._find(org, "shipments", shipment_id)
        if not ship:
            return {"ok": False, "error": "not_found", "message_ru": "Перевозка не найдена"}
        event_type = _str(body.get("event_type") or "comment")
        desc = _str(body.get("description") or body.get("comment") or EVENT_LABELS.get(event_type, "Событие"))
        loc = body.get("location") or body.get("current_location")
        saved = await self._add_event(
            org,
            shipment_id=shipment_id,
            event_type=event_type,
            description=desc,
            role=role,
            actor_id=actor_id,
            location=loc,
            document_id=body.get("document_id"),
            photo_id=body.get("photo_id"),
            source=_str(body.get("source") or "manual"),
            confirmation=body.get("confirmation"),
        )
        await self._audit(
            organization_id=org,
            action="event_added",
            entity_type="shipment",
            entity_id=shipment_id,
            role=role,
            actor_id=actor_id,
            new_value={"event_type": saved.get("event_type"), "source": saved.get("source"), "confirmation": saved.get("confirmation")},
            summary=desc,
        )
        if loc:
            await self._audit(
                organization_id=org,
                action="location_updated",
                entity_type="shipment",
                entity_id=shipment_id,
                role=role,
                actor_id=actor_id,
                new_value={"location": loc},
                summary="Ручное обновление местоположения",
            )
        return {"ok": True, "item": saved}

    async def _simple_create(
        self,
        organization_id: str,
        role: str | None,
        actor_id: str | None,
        *,
        kind: str,
        bag_key: str,
        required: tuple[str, ...],
        fields: tuple[str, ...],
        defaults: dict[str, Any],
        catalog_field: str | None = None,
        catalog_ids: frozenset[str] | None = None,
        body: dict[str, Any],
        audit_action: str,
    ) -> dict[str, Any]:
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        for key in required:
            if not _str(body.get(key)):
                return {"ok": False, "error": "validation", "message_ru": f"Укажите {key}", "field": key}
        if catalog_field and catalog_ids:
            val = _str(body.get(catalog_field) or defaults.get(catalog_field) or "").upper() if catalog_field in {"container_type", "status"} else _str(body.get(catalog_field) or defaults.get(catalog_field) or "")
            if catalog_field in {"container_type", "status", "container_status"}:
                val = _str(body.get(catalog_field) or defaults.get(catalog_field) or "").upper()
            if val not in catalog_ids and val.lower() not in {x.lower() for x in catalog_ids}:
                # allow lowercase ids for carrier/truck types
                if val.lower() in catalog_ids or val in catalog_ids:
                    pass
                else:
                    lower_map = {x.lower(): x for x in catalog_ids}
                    if val.lower() in lower_map:
                        val = lower_map[val.lower()]
                    else:
                        return {"ok": False, "error": "validation", "message_ru": f"Неизвестное значение {catalog_field}", "field": catalog_field}
            body = {**body, catalog_field: val if catalog_field in {"container_type", "status"} else val}
        item: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "workspace_id": self._workspace_id(org, body=body),
            "created_at": self._now(),
            "updated_at": self._now(),
            "created_by": actor_id or normalize_role(role),
            **defaults,
        }
        for field in fields:
            if field in body and body[field] not in (None, ""):
                item[field] = body[field]
        saved = await self._persist(kind, item)
        self._bag(org)[bag_key].insert(0, saved)
        await self._audit(organization_id=org, action=audit_action, entity_type=kind, entity_id=str(saved["id"]), role=role, actor_id=actor_id, new_value={k: saved.get(k) for k in required})
        return {"ok": True, "item": saved}

    async def _simple_update(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None, actor_id: str | None, *, kind: str, bag_key: str, fields: tuple[str, ...], missing_ru: str) -> dict[str, Any]:
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, bag_key, item_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": missing_ru}
        patch = {k: body[k] for k in fields if k in body}
        patch["updated_at"] = self._now()
        patch["updated_by"] = actor_id or normalize_role(role)
        item.update(patch)
        await self._persist_update(kind, item_id, patch)
        return {"ok": True, "item": item}

    async def _simple_list(self, organization_id: str, role: str | None, bag_key: str, query: dict[str, str] | None = None, search_fields: tuple[str, ...] = ()) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        items = self._scoped_rows(org, list(self._bag(org)[bag_key]), query)
        q = (query or {}).get("q") or (query or {}).get("search") or ""
        if q and search_fields:
            needle = q.upper()
            items = [i for i in items if needle in " ".join(str(i.get(f) or "") for f in search_fields).upper()]
        return {"ok": True, "items": items, "total": len(items)}

    async def create_carrier(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        ctype = _str(body.get("type") or "other").lower()
        if ctype not in CARRIER_TYPE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип перевозчика", "field": "type"}
        return await self._simple_create(
            organization_id,
            role,
            actor_id,
            kind="carrier",
            bag_key="carriers",
            required=("company_name",),
            fields=("company_name", "type", "country", "contact_person", "phone", "email", "telegram", "whatsapp", "website", "address", "tax_id", "notes", "rating", "active"),
            defaults={"type": ctype, "active": True},
            body={**body, "type": ctype},
            audit_action="carrier_created",
        )

    async def list_carriers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        return await self._simple_list(organization_id, role, "carriers", query, ("company_name", "country", "type"))

    async def update_carrier(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        return await self._simple_update(
            organization_id,
            item_id,
            body,
            role,
            actor_id,
            kind="carrier",
            bag_key="carriers",
            fields=("company_name", "type", "country", "contact_person", "phone", "email", "telegram", "whatsapp", "website", "address", "tax_id", "notes", "rating", "active"),
            missing_ru="Перевозчик не найден",
        )

    def _redact_driver(self, item: dict[str, Any], role: str | None) -> dict[str, Any]:
        out = dict(item)
        if not can(role, "pii"):
            out["passport_ref"] = "***"
            out["driver_license"] = "***"
            out["pii_restricted"] = True
        return out

    async def create_driver(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if _str(body.get("passport_ref") or body.get("driver_license")) and not (can(role, "pii") or can(role, "create")):
            return require(role, "pii") or {"ok": False, "error": "forbidden"}
        result = await self._simple_create(
            organization_id,
            role,
            actor_id,
            kind="driver",
            bag_key="drivers",
            required=("full_name",),
            fields=("full_name", "phone", "telegram", "whatsapp", "passport_ref", "driver_license", "carrier_id", "truck_id", "notes", "active"),
            defaults={"active": True},
            body=body,
            audit_action="driver_created",
        )
        if result.get("ok") and result.get("item"):
            result["item"] = self._redact_driver(result["item"], role)
        return result

    async def list_drivers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        result = await self._simple_list(organization_id, role, "drivers", query, ("full_name", "phone"))
        if result.get("ok"):
            result["items"] = [self._redact_driver(i, role) for i in result["items"]]
        return result

    async def update_driver(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if ("passport_ref" in body or "driver_license" in body) and not can(role, "pii"):
            return {"ok": False, "error": "forbidden", "message_ru": "Паспорт и водительское удостоверение доступны директору и администратору"}
        result = await self._simple_update(
            organization_id,
            item_id,
            body,
            role,
            actor_id,
            kind="driver",
            bag_key="drivers",
            fields=("full_name", "phone", "telegram", "whatsapp", "passport_ref", "driver_license", "carrier_id", "truck_id", "notes", "active"),
            missing_ru="Водитель не найден",
        )
        if result.get("ok") and result.get("item"):
            result["item"] = self._redact_driver(result["item"], role)
        return result

    async def create_truck(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        ttype = _str(body.get("type") or "truck").lower()
        if ttype not in TRUCK_TYPE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип транспорта", "field": "type"}
        return await self._simple_create(
            organization_id,
            role,
            actor_id,
            kind="truck",
            bag_key="trucks",
            required=("plate_number",),
            fields=("type", "plate_number", "country", "brand", "model", "vin", "carrier_id", "driver_id", "capacity", "notes"),
            defaults={"type": ttype},
            body={**body, "type": ttype},
            audit_action="truck_created",
        )

    async def list_trucks(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        return await self._simple_list(organization_id, role, "trucks", query, ("plate_number", "brand", "model"))

    async def update_truck(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        return await self._simple_update(
            organization_id,
            item_id,
            body,
            role,
            actor_id,
            kind="truck",
            bag_key="trucks",
            fields=("type", "plate_number", "country", "brand", "model", "vin", "carrier_id", "driver_id", "capacity", "notes"),
            missing_ru="Транспорт не найден",
        )

    async def create_port(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        unlocode = _str(body.get("unlocode")).upper() or None
        if unlocode and unlocode not in {p["unlocode"] for p in REFERENCE_PORTS}:
            # allow org-specific names without invented codes
            if len(unlocode) != 5:
                return {"ok": False, "error": "validation", "message_ru": "UN/LOCODE должен быть из проверенного справочника. Не указывайте выдуманный код."}
            return {"ok": False, "error": "validation", "message_ru": "Код порта отсутствует в проверенном справочнике UN/LOCODE. Оставьте поле пустым или выберите известный порт."}
        return await self._simple_create(
            organization_id,
            role,
            actor_id,
            kind="port",
            bag_key="ports",
            required=("name",),
            fields=("name", "unlocode", "country", "city", "address", "timezone", "notes"),
            defaults={},
            body={**body, "unlocode": unlocode} if unlocode else body,
            audit_action="port_created",
        )

    async def list_ports(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        own = [{**p, "source": "organization"} for p in self._bag(org)["ports"]]
        refs = [{**p, "id": p["unlocode"], "source": "reference", "notes": "Проверенный UN/LOCODE. Координаты не подставляются."} for p in REFERENCE_PORTS]
        items = own + refs
        q = ((query or {}).get("q") or "").upper()
        if q:
            items = [p for p in items if q in " ".join(str(p.get(k) or "") for k in ("name", "unlocode", "city", "country")).upper()]
        return {"ok": True, "items": items, "reference_only_note_ru": "Справочные порты не записываются в продакшен автоматически."}

    async def create_vessel(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        status = _str(body.get("status") or "PLANNED").upper()
        if status not in VESSEL_STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус судна"}
        result = await self._simple_create(
            organization_id,
            role,
            actor_id,
            kind="vessel",
            bag_key="vessels",
            required=("name",),
            fields=("name", "imo", "mmsi", "shipping_line", "voyage_number", "origin_port", "destination_port", "etd", "eta", "status", "tracking_url", "notes"),
            defaults={"status": status, "position_source": "manual"},
            body={**body, "status": status},
            audit_action="vessel_created",
        )
        if result.get("ok") and result.get("item"):
            result["item"]["eta_source_label_ru"] = "Введено вручную"
            result["item"]["live_ais"] = False
        return result

    async def list_vessels(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        result = await self._simple_list(organization_id, role, "vessels", query, ("name", "voyage_number", "shipping_line", "imo"))
        if result.get("ok"):
            for v in result["items"]:
                v["live_ais"] = False
                v["eta_source_label_ru"] = "Введено вручную"
        return result

    async def update_vessel(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        return await self._simple_update(
            organization_id,
            item_id,
            body,
            role,
            actor_id,
            kind="vessel",
            bag_key="vessels",
            fields=("name", "imo", "mmsi", "shipping_line", "voyage_number", "origin_port", "destination_port", "etd", "eta", "status", "tracking_url", "notes"),
            missing_ru="Судно не найдено",
        )

    async def create_container(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        ctype = _str(body.get("container_type") or "40HC").upper()
        if ctype not in CONTAINER_TYPE_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип контейнера"}
        status = _str(body.get("status") or "PLANNED").upper()
        if status not in CONTAINER_STATUS_IDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный статус контейнера"}
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        number = _str(body.get("container_number")).upper()
        if not number:
            return {"ok": False, "error": "validation", "message_ru": "Укажите номер контейнера", "field": "container_number"}
        dup = next((c for c in self._bag(org)["containers"] if str(c.get("container_number") or "").upper() == number), None)
        if dup:
            return {"ok": False, "error": "conflict", "message_ru": "Контейнер с таким номером уже есть", "existing_id": dup.get("id")}
        result = await self._simple_create(
            organization_id,
            role,
            actor_id,
            kind="container",
            bag_key="containers",
            required=("container_number",),
            fields=("container_number", "container_type", "shipping_line", "booking_number", "seal_number", "origin_port", "destination_port", "etd", "eta", "status", "current_location", "tracking_url", "notes", "responsible_manager_id"),
            defaults={"container_type": ctype, "status": status, "tracking_mode": "manual"},
            body={**body, "container_number": number, "container_type": ctype, "status": status},
            audit_action="container_created",
        )
        if result.get("ok") and result.get("item"):
            result["item"]["live_tracking"] = False
            result["item"]["eta_source_label_ru"] = "Введено вручную"
        return result

    async def list_containers(self, organization_id: str, role: str | None, query: dict[str, str] | None = None) -> dict[str, Any]:
        result = await self._simple_list(organization_id, role, "containers", query, ("container_number", "booking_number", "shipping_line"))
        if result.get("ok"):
            org = self._org(organization_id)
            for c in result["items"]:
                c["vehicle_count"] = len(self._container_vehicles(org, str(c.get("id")), active_only=True))
                c["live_tracking"] = False
        return result

    async def get_container(self, organization_id: str, container_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        item = self._find(org, "containers", container_id)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Контейнер не найден"}
        vehicles = self._container_vehicles(org, container_id)
        docs = [d for d in self._bag(org)["documents"] if not d.get("archived_at") and str(d.get("container_id") or "") == str(container_id)]
        costs: dict[str, Any] = {"restricted": True}
        shipment_ids = [str(s.get("id")) for s in self._bag(org)["shipments"] if str(s.get("container_id") or "") == str(container_id)]
        if can(role, "finance"):
            planned = actual = paid = unpaid = 0.0
            lines = []
            for sid in shipment_ids:
                snap = self._logistics_costs(org, shipment_id=sid)
                planned += snap["planned"]
                actual += snap["actual"]
                paid += snap["paid"]
                unpaid += snap["unpaid"]
                lines.extend(snap["lines"])
            costs = {
                "planned": round(planned, 2),
                "actual": round(actual, 2),
                "paid": round(paid, 2),
                "unpaid": round(unpaid, 2),
                "difference": round(actual - planned, 2),
                "currency": "USD",
                "from_records": True,
                "lines": lines,
            }
        return {
            "ok": True,
            "item": {**item, "live_tracking": False, "eta_source_label_ru": "Введено вручную"},
            "vehicles": vehicles,
            "documents": docs,
            "costs": costs,
            "shipments": [self._public_shipment(org, s, role) for s in self._bag(org)["shipments"] if str(s.get("container_id") or "") == str(container_id)],
        }

    async def update_container(self, organization_id: str, item_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        return await self._simple_update(
            organization_id,
            item_id,
            body,
            role,
            actor_id,
            kind="container",
            bag_key="containers",
            fields=("container_number", "container_type", "shipping_line", "booking_number", "seal_number", "origin_port", "destination_port", "etd", "eta", "status", "current_location", "tracking_url", "notes", "responsible_manager_id"),
            missing_ru="Контейнер не найден",
        )

    async def add_vehicle_to_container(self, organization_id: str, container_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        container = self._find(org, "containers", container_id)
        if not container:
            return {"ok": False, "error": "not_found", "message_ru": "Контейнер не найден"}
        vehicle_id = _str(body.get("vehicle_id"))
        if not vehicle_id or not self._find(org, "vehicles", vehicle_id):
            return {"ok": False, "error": "validation", "message_ru": "Автомобиль не найден"}
        existing = self._active_container_for_vehicle(org, vehicle_id)
        if existing and str(existing.get("id")) != str(container_id):
            if not body.get("reassign"):
                return {
                    "ok": False,
                    "error": "conflict",
                    "message_ru": "У автомобиля уже есть активный контейнер. Для переназначения передайте reassign=true (старое назначение сохранится в истории).",
                    "active_container_id": existing.get("id"),
                }
            for link in self._bag(org)["container_vehicles"]:
                if str(link.get("vehicle_id")) == vehicle_id and not link.get("released_at"):
                    link["released_at"] = self._now()
                    await self._persist_update("container_vehicle", str(link["id"]), {"released_at": link["released_at"]})
        already = next(
            (
                l
                for l in self._bag(org)["container_vehicles"]
                if str(l.get("container_id")) == str(container_id) and str(l.get("vehicle_id")) == vehicle_id and not l.get("released_at")
            ),
            None,
        )
        if already:
            return {"ok": False, "error": "conflict", "message_ru": "Автомобиль уже в этом контейнере"}
        link_item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "container_id": container_id,
            "vehicle_id": vehicle_id,
            "released_at": None,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        saved = await self._persist("container_vehicle", link_item)
        self._bag(org)["container_vehicles"].insert(0, saved)
        for ship in self._bag(org)["shipments"]:
            if str(ship.get("vehicle_id")) == vehicle_id and str(ship.get("status")) in ACTIVE_SHIPMENT_STATUSES:
                if str(ship.get("container_id") or "") != str(container_id):
                    ship["container_id"] = container_id
                    ship["updated_at"] = self._now()
                    await self._persist_update("shipment", str(ship["id"]), {"container_id": container_id, "updated_at": ship["updated_at"]})
                break
        await self._audit(organization_id=org, action="container_assigned", entity_type="container", entity_id=container_id, role=role, actor_id=actor_id, new_value={"vehicle_id": vehicle_id})
        return {"ok": True, "item": saved}

    async def list_notifications(self, organization_id: str, role: str | None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        return {"ok": True, "items": list(self._bag(org)["notifications"])[:100], "channel": "desk", "comms": "enterprise-comms boundary, not live spam"}

    async def logistics_settings(self, organization_id: str, role: str | None, body: dict[str, Any] | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        rows = self._bag(org)["logistics_settings"]
        current = rows[0] if rows else {"yellow_days": 3, "orange_days": 7, "default_origin_country": "US", "default_destination_country": "UA"}
        if body is not None:
            if not can(role, "admin"):
                return require(role, "admin") or {"ok": False, "error": "forbidden"}
            patch = {
                k: body[k]
                for k in (
                    "yellow_days",
                    "orange_days",
                    "default_origin_country",
                    "default_destination_country",
                    "default_origin_port",
                    "default_destination_port",
                    "require_manager_on_active_shipment",
                    "auto_create_suggested_tasks",
                    "manager_see_assigned_transport_cost",
                    "accountant_may_change_status",
                )
                if k in body
            }
            patch["updated_at"] = self._now()
            if rows:
                rows[0].update(patch)
                await self._persist_update("logistics_setting", str(rows[0]["id"]), patch)
                current = rows[0]
            else:
                item = {"id": str(uuid.uuid4()), "organization_id": org, "tenant_id": org, "workspace_id": org, "created_at": self._now(), **current, **patch}
                saved = await self._persist("logistics_setting", item)
                rows.insert(0, saved)
                current = saved
        current = {**DEFAULT_LOGISTICS_POLICY, **current}
        return {"ok": True, "item": current, "policy": self._logistics_policy(org), "catalogs": self.catalogs(), "can_admin": can(role, "admin")}

    async def seed_demo_logistics(self, organization_id: str, body: dict[str, Any], role: str | None, actor_id: str | None = None) -> dict[str, Any]:
        if not body.get("confirm_demo"):
            return {"ok": False, "error": "validation", "message_ru": "Для демо-сценария передайте confirm_demo=true. Демо никогда не смешивается с продакшен-записями без явного флага."}
        denied = self._write_denied(role)
        if denied:
            return denied
        org = self._org(organization_id)
        await self.ensure_hydrated(org)
        vehicle = await self.create_vehicle(
            org,
            {
                "vin": "WBAFR9C50DD123456",
                "allow_nonstandard_vin": True,
                "manufacturer": "BMW",
                "model": "X5",
                "year": 2013,
                "purchase_country": "US",
                "auction_name": "Copart (demo)",
                "auction_url": "https://demo.invalid/lot/x5",
                "status": "IN_CONTAINER",
                "location_current": "Контейнер, порт Savannah",
                "origin_port": "Savannah",
                "destination_port": "Odesa",
                "assigned_manager_id": "demo-manager",
            },
            role if can(role, "vin_override") else "auto_director",
            actor_id,
        )
        if not vehicle.get("ok"):
            return vehicle
        vid = str(vehicle["item"]["id"])
        # mark demo on vehicle
        vrow = self._find(org, "vehicles", vid)
        if vrow:
            vrow["is_demo"] = True
            vrow["notes"] = "DEMO — AUTO 1.1 logistics scenario. Not a production record."
        carrier = await self.create_carrier(org, {"company_name": "DEMO Inland Carrier", "type": "truck", "country": "US"}, role, actor_id)
        forwarder = await self.create_carrier(org, {"company_name": "DEMO Container Line", "type": "container_forwarder", "country": "US"}, role, actor_id)
        driver = await self.create_driver(org, {"full_name": "Demo Driver", "phone": "+10000000000", "carrier_id": (carrier.get("item") or {}).get("id")}, role, actor_id)
        truck = await self.create_truck(org, {"type": "car_transporter", "plate_number": "DEMO-001", "country": "US", "brand": "Freightliner"}, role, actor_id)
        port_origin = await self.create_port(org, {"name": "Savannah", "unlocode": "USSAV", "country": "US", "city": "Savannah"}, role, actor_id)
        port_dest = await self.create_port(org, {"name": "Odesa", "unlocode": "UAODS", "country": "UA", "city": "Odesa"}, role, actor_id)
        vessel = await self.create_vessel(
            org,
            {"name": "DEMO Vessel Atlantic", "shipping_line": "Demo Line", "voyage_number": "D-001", "origin_port": "USSAV", "destination_port": "UAODS", "status": "AT_SEA", "etd": "2026-08-01", "eta": "2026-08-25"},
            role,
            actor_id,
        )
        container = await self.create_container(
            org,
            {
                "container_number": "DEMO1234567",
                "container_type": "40HC",
                "shipping_line": "Demo Line",
                "booking_number": "BKG-DEMO-1",
                "origin_port": "USSAV",
                "destination_port": "UAODS",
                "status": "IN_TRANSIT",
                "etd": "2026-08-01",
                "eta": "2026-08-25",
            },
            role,
            actor_id,
        )
        cid = str((container.get("item") or {}).get("id") or "")
        ship = await self.create_shipment(
            org,
            {
                "vehicle_id": vid,
                "shipment_type": "CONTAINER",
                "status": "SEA_TRANSIT",
                "origin_country": "US",
                "origin_location": "Copart auction yard (demo)",
                "destination_country": "UA",
                "destination_location": "Одесса / склад",
                "carrier_id": (forwarder.get("item") or {}).get("id"),
                "container_id": cid,
                "vessel_id": (vessel.get("item") or {}).get("id"),
                "origin_port_id": "USSAV",
                "destination_port_id": "UAODS",
                "booking_number": "BKG-DEMO-1",
                "bill_of_lading_number": "BL-DEMO-1",
                "etd": "2026-08-01",
                "eta": "2026-08-25",
                "planned_eta": "2026-08-22",
                "current_eta": "2026-08-25",
                "responsible_manager_id": "demo-manager",
                "is_demo": True,
                "notes": "DEMO USA auction → inland → Savannah → container → vessel → Odesa",
            },
            role,
            actor_id,
        )
        sid = str((ship.get("item") or {}).get("id") or "")
        if cid and vid:
            await self.add_vehicle_to_container(org, cid, {"vehicle_id": vid}, role, actor_id)
        await self.add_shipment_event(org, sid, {"event_type": "vehicle_won", "description": "Автомобиль выигран на аукционе (demo)"}, role, actor_id)
        await self.add_shipment_event(org, sid, {"event_type": "vehicle_collected", "description": "Забран inland carrier (demo)"}, role, actor_id)
        await self.add_shipment_event(org, sid, {"event_type": "loaded_on_vessel", "description": "Погружен на судно (demo)"}, role, actor_id)
        for rec in (
            self._find(org, "carriers", str((carrier.get("item") or {}).get("id") or "")),
            self._find(org, "carriers", str((forwarder.get("item") or {}).get("id") or "")),
            self._find(org, "drivers", str((driver.get("item") or {}).get("id") or "")),
            self._find(org, "trucks", str((truck.get("item") or {}).get("id") or "")),
            self._find(org, "ports", str((port_origin.get("item") or {}).get("id") or "")),
            self._find(org, "ports", str((port_dest.get("item") or {}).get("id") or "")),
            self._find(org, "vessels", str((vessel.get("item") or {}).get("id") or "")),
            self._find(org, "containers", cid),
            self._find(org, "shipments", sid),
        ):
            if rec:
                rec["is_demo"] = True
        return {
            "ok": True,
            "demo": True,
            "label_ru": "Демо-сценарий AUTO 1.1. Не продакшен.",
            "vehicle": vehicle.get("item"),
            "shipment": ship.get("item"),
            "container": container.get("item"),
            "vessel": vessel.get("item"),
        }
