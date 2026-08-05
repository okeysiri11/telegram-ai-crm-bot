"""Unified Permission Engine — Sprint 30.0.

Additive facade over existing IAM / role / PermissionManager surfaces.
Does not replace platform_identity.permission_service or platform_security.permissions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from platform_security.permissions import permission_manager
from platform_security.roles import role_manager


@dataclass
class PermissionContext:
    principal_id: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    organization_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    auth_method: str | None = None

    @classmethod
    def from_principal(cls, principal: Any, *, tenant_id: str | None = None) -> PermissionContext:
        return cls(
            principal_id=str(getattr(principal, "principal_id", "") or ""),
            roles=list(getattr(principal, "roles", []) or []),
            permissions=list(getattr(principal, "permissions", []) or []),
            tenant_id=tenant_id,
            auth_method=getattr(getattr(principal, "auth_method", None), "value", None)
            or getattr(principal, "auth_method", None),
        )


class PermissionCache:
    def __init__(self, *, ttl_seconds: float = 60.0) -> None:
        self._ttl = ttl_seconds
        self._entries: dict[str, tuple[float, set[str]]] = {}

    def get(self, key: str) -> set[str] | None:
        hit = self._entries.get(key)
        if hit is None:
            return None
        expires, value = hit
        if time.monotonic() > expires:
            self._entries.pop(key, None)
            return None
        return set(value)

    def set(self, key: str, permissions: set[str]) -> None:
        self._entries[key] = (time.monotonic() + self._ttl, set(permissions))

    def clear(self) -> None:
        self._entries.clear()


class RoleResolver:
    def resolve(self, roles: list[str]) -> set[str]:
        return set(role_manager.effective_permissions(roles))


class PolicyEvaluator:
    """Simple allow/deny policy evaluator (RBAC + optional attribute match)."""

    def evaluate(
        self,
        *,
        effective: set[str],
        permission: str,
        resource: str | None = None,
        attributes: dict[str, Any] | None = None,
        required_attributes: dict[str, Any] | None = None,
    ) -> bool:
        from platform_security.models import SecurityPrincipal

        principal = SecurityPrincipal(
            principal_id="policy-eval",
            roles=[],
            permissions=sorted(effective),
        )
        if not permission_manager.check(principal, permission, resource=resource):
            return False
        if required_attributes:
            attrs = attributes or {}
            for key, expected in required_attributes.items():
                if attrs.get(key) != expected:
                    return False
        return True


class PermissionResolver:
    def __init__(
        self,
        *,
        role_resolver: RoleResolver | None = None,
        policy_evaluator: PolicyEvaluator | None = None,
        cache: PermissionCache | None = None,
    ) -> None:
        self.roles = role_resolver or RoleResolver()
        self.policies = policy_evaluator or PolicyEvaluator()
        self.cache = cache or PermissionCache()

    def effective_permissions(self, ctx: PermissionContext) -> set[str]:
        cache_key = f"{ctx.principal_id}|{','.join(sorted(ctx.roles))}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        effective = set(ctx.permissions)
        effective.update(self.roles.resolve(ctx.roles))
        self.cache.set(cache_key, effective)
        return effective

    def allow(
        self,
        ctx: PermissionContext,
        permission: str,
        *,
        resource: str | None = None,
        required_attributes: dict[str, Any] | None = None,
    ) -> bool:
        effective = self.effective_permissions(ctx)
        return self.policies.evaluate(
            effective=effective,
            permission=permission,
            resource=resource,
            attributes=ctx.attributes,
            required_attributes=required_attributes,
        )


# Module singletons
permission_cache = PermissionCache()
role_resolver = RoleResolver()
policy_evaluator = PolicyEvaluator()
permission_resolver = PermissionResolver(
    role_resolver=role_resolver,
    policy_evaluator=policy_evaluator,
    cache=permission_cache,
)

__all__ = [
    "PermissionContext",
    "PermissionCache",
    "PermissionResolver",
    "PolicyEvaluator",
    "RoleResolver",
    "permission_resolver",
    "permission_cache",
    "role_resolver",
    "policy_evaluator",
]
