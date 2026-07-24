"""Validation Engine — Sprint 22.9."""

from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = {
    "clients": ("name",),
    "employees": ("name", "role"),
    "services": ("name", "price"),
    "products": ("name", "sku"),
    "inventory": ("sku", "qty"),
    "certificates": ("code", "face_value"),
    "memberships": ("customer_id", "visits_limit"),
    "bonuses": ("customer_id", "points"),
    "schedules": ("employee_id", "start", "end"),
}


class ValidationEngine:
    def validate(self, *, entity: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        required = REQUIRED_FIELDS.get(entity, ("id",))
        issues: list[dict[str, Any]] = []
        seen: set[str] = set()
        for i, row in enumerate(rows):
            missing = [f for f in required if not row.get(f) and row.get(f) != 0]
            if missing:
                issues.append({"row": i, "type": "missing_fields", "fields": missing, "fix": f"fill {', '.join(missing)}"})
            key = str(row.get("id") or row.get("sku") or row.get("code") or row.get("name") or "")
            if key:
                if key in seen:
                    issues.append({"row": i, "type": "duplicate", "key": key, "fix": "remove or merge duplicate"})
                seen.add(key)
            # format checks
            if entity in ("services", "products", "certificates", "bonuses") and "price" in row:
                try:
                    float(row["price"])
                except (TypeError, ValueError):
                    issues.append({"row": i, "type": "format", "field": "price", "fix": "use numeric price"})
            if entity == "services" and row.get("price") is not None:
                try:
                    float(row["price"])
                except (TypeError, ValueError):
                    issues.append({"row": i, "type": "format", "field": "price", "fix": "use numeric price"})
            if entity == "inventory" and row.get("qty") is not None:
                try:
                    float(row["qty"])
                except (TypeError, ValueError):
                    issues.append({"row": i, "type": "format", "field": "qty", "fix": "use numeric qty"})
        structure_ok = all(isinstance(r, dict) for r in rows)
        if not structure_ok:
            issues.append({"row": None, "type": "structure", "fix": "each row must be an object"})
        return {
            "entity": entity,
            "row_count": len(rows),
            "valid": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues,
            "report": "ok" if not issues else "needs_fixes",
            "suggested_fixes": [i.get("fix") for i in issues if i.get("fix")],
        }
