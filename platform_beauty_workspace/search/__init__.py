"""Smart search — Sprint 22.3."""

from __future__ import annotations

from typing import Any

from platform_beauty_workspace.models import SEARCH_TARGETS


class SmartSearch:
    def search(
        self,
        *,
        query: str,
        customers: list[dict[str, Any]] | None = None,
        services: list[dict[str, Any]] | None = None,
        employees: list[dict[str, Any]] | None = None,
        appointments: list[dict[str, Any]] | None = None,
        certificates: list[dict[str, Any]] | None = None,
        memberships: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        q = (query or "").strip().lower()
        if not q:
            raise ValueError("search query is required")
        results: dict[str, list[dict[str, Any]]] = {t: [] for t in SEARCH_TARGETS}

        def match(item: dict[str, Any], fields: tuple[str, ...]) -> bool:
            blob = " ".join(str(item.get(f, "")) for f in fields).lower()
            return q in blob

        for c in customers or []:
            if match(c, ("name", "phone", "customer_id")):
                results["customers"].append(c)
                if c.get("phone"):
                    results["phones"].append({"phone": c.get("phone"), "customer_id": c.get("customer_id")})
        for s in services or []:
            if match(s, ("name", "category", "service_id")):
                results["services"].append(s)
        for e in employees or []:
            if match(e, ("name", "role", "specialization", "employee_id")):
                results["employees"].append(e)
        for a in appointments or []:
            if match(a, ("appointment_id", "customer_id", "service_id", "status")):
                results["appointments"].append(a)
        for cert in certificates or []:
            if match(cert, ("code", "customer_id", "name")):
                results["certificates"].append(cert)
        for m in memberships or []:
            if match(m, ("code", "customer_id", "name")):
                results["memberships"].append(m)

        total = sum(len(v) for v in results.values())
        return {"query": query, "targets": list(SEARCH_TARGETS), "results": results, "total": total}
