"""Gift Certificates portal view — Sprint 22.8."""

from __future__ import annotations

from typing import Any


class GiftCertificatesView:
    def list_certs(self, certificates: list[dict[str, Any]]) -> dict[str, Any]:
        items = []
        for c in certificates:
            items.append(
                {
                    "certificate_id": c.get("certificate_id"),
                    "balance": c.get("balance", c.get("face_value", 0)),
                    "expires_at": c.get("expires_at"),
                    "status": c.get("status", "active"),
                    "usable": c.get("status") in ("active", "issued") and float(c.get("balance", 0) or 0) > 0,
                }
            )
        return {"certificates": items, "count": len(items), "commerce_ref": "commerce_core"}
