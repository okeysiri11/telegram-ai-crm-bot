# ValidationProvider — centralized field and permission validation.

from __future__ import annotations

import re
from typing import Any

from platform_sdk.exceptions import ValidationError

_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.IGNORECASE)
_PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


class ValidationProvider:
    @staticmethod
    def validate_vin(value: str | None, *, required: bool = False) -> str | None:
        if not value or not str(value).strip():
            if required:
                raise ValidationError("VIN is required", field="vin")
            return None
        vin = str(value).strip().upper()
        if not _VIN_RE.match(vin):
            raise ValidationError("Invalid VIN format (17 alphanumeric characters)", field="vin")
        return vin

    @staticmethod
    def validate_phone(value: str | None, *, required: bool = False) -> str | None:
        if not value or not str(value).strip():
            if required:
                raise ValidationError("Phone is required", field="phone")
            return None
        phone = str(value).strip().replace(" ", "").replace("-", "")
        if not _PHONE_RE.match(phone):
            raise ValidationError("Invalid phone format", field="phone")
        return phone

    @staticmethod
    def validate_required(data: dict[str, Any], fields: list[str]) -> None:
        missing = [f for f in fields if not data.get(f)]
        if missing:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing)}",
                field=missing[0],
            )

    @staticmethod
    async def validate_permission(
        *,
        actor_telegram_id: int,
        permission: str,
        vertical: str | None = None,
    ) -> bool:
        from platform_legacy import legacy

        allowed = await legacy.permissions.user_has_permission(
            actor_telegram_id,
            permission,
        )
        if not allowed:
            raise ValidationError(
                f"Permission denied: {permission}",
                field="permission",
            )
        return True

    @staticmethod
    def validate_policy(data: dict[str, Any], policy: dict[str, Any]) -> None:
        """Apply vertical validation_policy config."""
        required = list(policy.get("required_fields") or [])
        if required:
            ValidationProvider.validate_required(data, required)
        if policy.get("require_vin") and data.get("vin") is not None:
            ValidationProvider.validate_vin(data.get("vin"), required=bool(policy.get("require_vin")))
        if policy.get("require_phone"):
            ValidationProvider.validate_phone(data.get("phone"), required=True)


validation_provider = ValidationProvider()
