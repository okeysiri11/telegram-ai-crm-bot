"""Client portal security — Sprint 22.8."""

from __future__ import annotations

from typing import Any


class PortalSecurity:
    def enable_2fa(self, *, customer_id: str, method: str = "sms") -> dict[str, Any]:
        if not customer_id:
            raise ValueError("customer_id is required")
        return {"customer_id": customer_id, "two_factor": True, "method": method, "status": "enabled"}

    def register_device(self, *, customer_id: str, device_id: str, platform: str) -> dict[str, Any]:
        if not device_id:
            raise ValueError("device_id is required")
        return {
            "customer_id": customer_id,
            "device_id": device_id,
            "platform": platform,
            "trusted": True,
        }

    def consent(self, *, customer_id: str, accepted: bool = True) -> dict[str, Any]:
        return {
            "customer_id": customer_id,
            "personal_data_consent": bool(accepted),
            "version": "1.0",
        }

    def login_event(self, *, customer_id: str, device_id: str = "", success: bool = True) -> dict[str, Any]:
        return {
            "customer_id": customer_id,
            "device_id": device_id or None,
            "success": success,
            "journal": True,
        }
