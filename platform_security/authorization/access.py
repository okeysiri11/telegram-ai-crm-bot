"""RBAC + ABAC — Sprint 21.4."""

from __future__ import annotations

from typing import Any

from platform_security.models import ABAC_ATTRIBUTES


class AccessControl:
    def __init__(self) -> None:
        self._roles: dict[str, set[str]] = {}
        self._policies: list[dict[str, Any]] = []

    def grant_role(self, principal: str, role: str) -> dict[str, Any]:
        self._roles.setdefault(principal, set()).add(role)
        return {"principal": principal, "roles": sorted(self._roles[principal])}

    def define_policy(self, *, name: str, attributes: dict[str, Any], effect: str = "allow") -> dict[str, Any]:
        unknown = [k for k in attributes if k not in ABAC_ATTRIBUTES]
        if unknown:
            raise ValueError(f"unknown ABAC attributes: {', '.join(unknown)}")
        policy = {"name": name, "attributes": attributes, "effect": effect}
        self._policies.append(policy)
        return policy

    def authorize(
        self,
        *,
        principal: str,
        roles_required: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        roles = self._roles.get(principal, set())
        rbac_ok = True
        if roles_required:
            rbac_ok = all(r in roles for r in roles_required)
        abac_ok = True
        attrs = attributes or {}
        for policy in self._policies:
            if policy["effect"] != "allow":
                continue
            for key, expected in policy["attributes"].items():
                if attrs.get(key) != expected:
                    abac_ok = False
                    break
        allowed = rbac_ok and (abac_ok if self._policies else True)
        return {
            "allowed": allowed,
            "rbac_ok": rbac_ok,
            "abac_ok": abac_ok,
            "roles": sorted(roles),
            "attributes_checked": list(ABAC_ATTRIBUTES),
        }

    def status(self) -> dict[str, Any]:
        return {"principals": len(self._roles), "policies": len(self._policies)}
