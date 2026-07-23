"""Incident management — severity, timeline, SLA, resolution."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.observability.models import INCIDENT_STATUSES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IncidentManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def open(
        self,
        *,
        service: str,
        severity: str = "error",
        owner: str = "ops",
        root_cause: str = "",
        sla_minutes: int = 60,
    ) -> dict[str, Any]:
        if not service:
            raise ValidationError("service required")
        iid = _id("obs_inc")
        return self.store.obs_incidents.save(
            iid,
            {
                "incident_id": iid,
                "service": service,
                "severity": severity,
                "root_cause": root_cause,
                "timeline": [{"event": "opened", "at": _now()}],
                "status": "open",
                "owner": owner,
                "resolution": "",
                "sla_minutes": int(sla_minutes),
                "at": _now(),
            },
        )

    def update(
        self,
        *,
        incident_id: str,
        status: str = "",
        root_cause: str = "",
        resolution: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        inc = self.store.obs_incidents.get(incident_id)
        if inc is None:
            raise NotFoundError(f"incident not found: {incident_id}")
        if status:
            st = status.lower().strip()
            if st not in INCIDENT_STATUSES:
                raise ValidationError(f"status must be one of {list(INCIDENT_STATUSES)}")
            inc["status"] = st
        if root_cause:
            inc["root_cause"] = root_cause
        if resolution:
            inc["resolution"] = resolution
        timeline = list(inc.get("timeline") or [])
        timeline.append({"event": note or status or "update", "at": _now()})
        inc["timeline"] = timeline
        inc["at"] = _now()
        return self.store.obs_incidents.save(incident_id, inc)

    def status(self) -> dict[str, Any]:
        return {"incidents": self.store.obs_incidents.count(), "statuses": list(INCIDENT_STATUSES)}
