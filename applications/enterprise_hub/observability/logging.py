"""Centralized logging with search by correlation, user, service, agent."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.observability.models import LOG_KINDS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CentralizedLogging:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def write(
        self,
        *,
        kind: str,
        message: str,
        service: str = "",
        user: str = "",
        ai_agent: str = "",
        correlation_id: str = "",
    ) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in LOG_KINDS:
            raise ValidationError(f"kind must be one of {list(LOG_KINDS)}")
        if not message:
            raise ValidationError("message required")
        lid = _id("obs_log")
        corr = correlation_id or _id("corr")
        return self.store.obs_logs.save(
            lid,
            {
                "log_id": lid,
                "kind": k,
                "message": message,
                "service": service,
                "user": user,
                "ai_agent": ai_agent,
                "correlation_id": corr,
                "at": _now(),
            },
        )

    def search(
        self,
        *,
        query: str = "",
        correlation_id: str = "",
        user: str = "",
        service: str = "",
        ai_agent: str = "",
    ) -> dict[str, Any]:
        matches = []
        for item in self.store.obs_logs.list_all():
            if not isinstance(item, dict):
                continue
            if correlation_id and item.get("correlation_id") != correlation_id:
                continue
            if user and item.get("user") != user:
                continue
            if service and item.get("service") != service:
                continue
            if ai_agent and item.get("ai_agent") != ai_agent:
                continue
            if query and query.lower() not in str(item.get("message", "")).lower():
                continue
            matches.append(item)
        sid = _id("obs_lsearch")
        return self.store.obs_log_searches.save(
            sid,
            {
                "search_id": sid,
                "query": query,
                "correlation_id": correlation_id,
                "count": len(matches),
                "results": matches[:50],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "logs": self.store.obs_logs.count(),
            "searches": self.store.obs_log_searches.count(),
            "kinds": list(LOG_KINDS),
        }
