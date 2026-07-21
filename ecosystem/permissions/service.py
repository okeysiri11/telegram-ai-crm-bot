# Permission service — roles and access control.

from __future__ import annotations

from events.publisher import publish

from ecosystem.events import RoleAssignedEvent
from ecosystem.permissions.models import BUILTIN_ROLE_PERMISSIONS, Role, RoleAssignment, SystemRole
from ecosystem.shared.exceptions import AuthorizationError, NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class PermissionService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._seed_builtin_roles()

    def _seed_builtin_roles(self) -> None:
        if self._store.roles.count() > 0:
            return
        for system_role, permissions in BUILTIN_ROLE_PERMISSIONS.items():
            role = Role(name=system_role.value, system_role=system_role, permissions=list(permissions))
            self._store.roles.save(role.role_id, role)

    def _ensure_seeded(self) -> None:
        if self._store.roles.count() == 0:
            self._seed_builtin_roles()

    def get_system_role(self, system_role: SystemRole, organization_id: str = "") -> Role:
        self._ensure_seeded()
        for role in self._store.roles.list_all():
            if role.system_role == system_role and (not organization_id or role.organization_id in ("", organization_id)):
                return role
        role = Role(
            name=system_role.value,
            system_role=system_role,
            organization_id=organization_id,
            permissions=list(BUILTIN_ROLE_PERMISSIONS[system_role]),
        )
        self._store.roles.save(role.role_id, role)
        return role

    def create_custom_role(self, name: str, permissions: list[str], *, organization_id: str = "") -> Role:
        role = Role(name=name, is_custom=True, organization_id=organization_id, permissions=list(permissions))
        self._store.roles.save(role.role_id, role)
        return role

    async def assign_role(self, user_id: str, role_id: str, organization_id: str = "") -> RoleAssignment:
        role = self.get_role(role_id)
        assignment = RoleAssignment(user_id=user_id, role_id=role_id, organization_id=organization_id)
        self._store.role_assignments.save(assignment.assignment_id, assignment)
        await publish(RoleAssignedEvent(user_id=user_id, role_id=role_id, role_name=role.name, organization_id=organization_id))
        return assignment

    def get_role(self, role_id: str) -> Role:
        role = self._store.roles.get(role_id)
        if role is None:
            raise NotFoundError("Role", role_id)
        return role

    def list_roles(self, *, organization_id: str = "") -> list[Role]:
        self._ensure_seeded()
        roles = self._store.roles.list_all()
        if organization_id:
            return [r for r in roles if r.organization_id in ("", organization_id)]
        return roles

    def user_roles(self, user_id: str, *, organization_id: str = "") -> list[Role]:
        assignments = [a for a in self._store.role_assignments.list_all() if a.user_id == user_id]
        if organization_id:
            assignments = [a for a in assignments if a.organization_id in ("", organization_id)]
        return [self.get_role(a.role_id) for a in assignments]

    def check_permission(self, user_id: str, permission: str, *, organization_id: str = "") -> bool:
        roles = self.user_roles(user_id, organization_id=organization_id)
        for role in roles:
            if "*" in role.permissions:
                return True
            if permission in role.permissions:
                return True
            prefix = permission.split(":")[0]
            if f"{prefix}:*" in role.permissions:
                return True
        return False

    def require_permission(self, user_id: str, permission: str, *, organization_id: str = "") -> None:
        if not self.check_permission(user_id, permission):
            raise AuthorizationError(f"Missing permission: {permission}")


permission_service = PermissionService()
