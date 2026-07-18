# Policy engine — RBAC, inheritance, resource-level and custom policies.

from __future__ import annotations

import fnmatch
import logging
import uuid
from typing import Any

from platform_identity.exceptions import AuthorizationError, PolicyError
from platform_identity.models import PlatformRole, PolicyRule, Principal, ResourceRef
from platform_identity.permission_service import permission_service
from platform_identity.role_service import role_service

logger = logging.getLogger(__name__)


class PolicyEngine:
    def __init__(self) -> None:
        self._custom_policies: dict[str, PolicyRule] = {}

    def reset(self) -> None:
        self._custom_policies.clear()

    def add_policy(self, policy: PolicyRule) -> PolicyRule:
        self._custom_policies[policy.policy_id] = policy
        return policy

    def create_policy(
        self,
        *,
        name: str,
        effect: str,
        permissions: list[str],
        roles: list[str] | None = None,
        principal_ids: list[str] | None = None,
        resources: list[ResourceRef] | None = None,
        tenant_id: str | None = None,
    ) -> PolicyRule:
        if effect not in {"allow", "deny"}:
            raise PolicyError(f"Invalid policy effect: {effect}")
        policy = PolicyRule(
            policy_id=str(uuid.uuid4()),
            name=name,
            effect=effect,
            permissions=permissions,
            roles=roles or [],
            principal_ids=principal_ids or [],
            resources=resources or [],
            tenant_id=tenant_id,
        )
        return self.add_policy(policy)

    def list_policies(self) -> list[PolicyRule]:
        return list(self._custom_policies.values())

    def remove_policy(self, policy_id: str) -> bool:
        return self._custom_policies.pop(policy_id, None) is not None

    async def authorize(
        self,
        principal: Principal,
        permission: str,
        *,
        resource: ResourceRef | None = None,
    ) -> bool:
        if principal.is_owner or PlatformRole.OWNER.value in principal.roles:
            return True

        if principal.tenant_id and resource and resource.tenant_id:
            if resource.tenant_id != principal.tenant_id:
                return False

        expanded_roles = role_service.expand_roles(principal.roles)
        effective_perms = set(principal.permissions)
        for role in expanded_roles:
            effective_perms.update(role_service.permissions_for_role(role))

        if permission in effective_perms:
            if not self._custom_policies:
                return True
        elif not await self._legacy_permission_check(principal, permission):
            if not self._matches_custom_allow(principal, permission, resource, expanded_roles):
                await self._log_denied(principal, permission, resource)
                return False

        if self._matches_custom_deny(principal, permission, resource, expanded_roles):
            await self._log_denied(principal, permission, resource)
            return False

        return True

    async def assert_authorized(
        self,
        principal: Principal,
        permission: str,
        *,
        resource: ResourceRef | None = None,
    ) -> None:
        if not await self.authorize(principal, permission, resource=resource):
            raise AuthorizationError(
                f"Principal {principal.principal_id} denied permission {permission}"
            )

    async def authorize_realtime_channel(self, principal: Principal, channel: str) -> bool:
        perm = permission_service.channel_permission(channel)
        return await self.authorize(principal, perm)

    async def assert_realtime_channel(self, principal: Principal, channel: str) -> None:
        if not await self.authorize_realtime_channel(principal, channel):
            raise AuthorizationError(
                f"Principal {principal.principal_id} cannot subscribe to channel {channel}"
            )

    def permission_matrix(self) -> dict[str, dict[str, bool]]:
        from platform_realtime.models import ALL_CHANNELS

        roles = role_service.list_roles()
        matrix: dict[str, dict[str, bool]] = {}
        for channel in ALL_CHANNELS:
            perm = permission_service.channel_permission(channel)
            matrix[channel] = {}
            for role in roles:
                perms = role_service.permissions_for_role(role)
                matrix[channel][role] = perm in perms or role == PlatformRole.OWNER.value
        return matrix

    async def _legacy_permission_check(self, principal: Principal, permission: str) -> bool:
        legacy = permission_service.legacy_code(permission)
        if legacy is None or principal.telegram_id is None:
            return False
        try:
            from platform_legacy import legacy

            return await legacy.permissions.user_has_permission(
                principal.telegram_id,
                legacy,
            )
        except Exception:
            return False

    def _matches_custom_allow(
        self,
        principal: Principal,
        permission: str,
        resource: ResourceRef | None,
        roles: list[str],
    ) -> bool:
        for policy in self._custom_policies.values():
            if policy.effect != "allow":
                continue
            if not self._policy_applies(policy, principal, permission, resource, roles):
                continue
            return True
        return False

    def _matches_custom_deny(
        self,
        principal: Principal,
        permission: str,
        resource: ResourceRef | None,
        roles: list[str],
    ) -> bool:
        for policy in self._custom_policies.values():
            if policy.effect != "deny":
                continue
            if self._policy_applies(policy, principal, permission, resource, roles):
                return True
        return False

    def _policy_applies(
        self,
        policy: PolicyRule,
        principal: Principal,
        permission: str,
        resource: ResourceRef | None,
        roles: list[str],
    ) -> bool:
        if policy.tenant_id and principal.tenant_id and policy.tenant_id != principal.tenant_id:
            return False

        principal_match = (
            not policy.principal_ids and not policy.roles
        ) or principal.principal_id in policy.principal_ids or any(r in policy.roles for r in roles)

        if not principal_match:
            return False

        perm_match = any(fnmatch.fnmatch(permission, pattern) for pattern in policy.permissions)
        if not perm_match:
            return False

        if policy.resources and resource:
            return any(
                r.type == resource.type and (r.id is None or r.id == resource.id)
                for r in policy.resources
            )
        return True

    async def _log_denied(
        self,
        principal: Principal,
        permission: str,
        resource: ResourceRef | None,
    ) -> None:
        from platform_identity.audit_hooks import iam_audit

        await iam_audit.log_authorization_failure(
            principal=principal,
            permission=permission,
            resource=resource,
        )


policy_engine = PolicyEngine()
