# Organization service — org hierarchy, membership, invitations.

from __future__ import annotations

import secrets

from events.publisher import publish

from ecosystem.events import OrganizationCreatedEvent, WorkspaceCreatedEvent
from ecosystem.organizations.models import (
    Department,
    Invitation,
    Membership,
    Organization,
    Project,
    Team,
    Workspace,
)
from ecosystem.permissions.models import Role, SystemRole
from ecosystem.permissions.service import PermissionService, permission_service
from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class OrganizationService:
    def __init__(
        self,
        store: EcosystemStore | None = None,
        permissions: PermissionService | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self._permissions = permissions or permission_service

    async def create_organization(
        self,
        *,
        name: str,
        owner_id: str,
        tenant_id: str = "",
        slug: str = "",
    ) -> Organization:
        org = Organization(
            name=name,
            slug=slug or name.lower().replace(" ", "-"),
            owner_id=owner_id,
            tenant_id=tenant_id,
        )
        self._store.organizations.save(org.organization_id, org)
        owner_role = self._permissions.get_system_role(SystemRole.ORGANIZATION_OWNER, org.organization_id)
        await self._permissions.assign_role(user_id=owner_id, role_id=owner_role.role_id, organization_id=org.organization_id)
        await publish(OrganizationCreatedEvent(organization_id=org.organization_id, owner_id=owner_id, tenant_id=tenant_id))
        return org

    async def create_workspace(
        self,
        *,
        organization_id: str,
        name: str,
        owner_id: str,
        is_default: bool = False,
    ) -> Workspace:
        org = self.get_organization(organization_id)
        workspace = Workspace(
            organization_id=org.organization_id,
            name=name,
            slug=name.lower().replace(" ", "-"),
            owner_id=owner_id,
            is_default=is_default,
        )
        self._store.workspaces.save(workspace.workspace_id, workspace)
        await publish(WorkspaceCreatedEvent(workspace_id=workspace.workspace_id, organization_id=organization_id, owner_id=owner_id))
        return workspace

    def create_department(self, organization_id: str, name: str, *, parent_id: str = "") -> Department:
        self.get_organization(organization_id)
        dept = Department(organization_id=organization_id, name=name, parent_id=parent_id)
        self._store.departments.save(dept.department_id, dept)
        return dept

    def create_team(self, organization_id: str, name: str, *, department_id: str = "", lead_id: str = "") -> Team:
        self.get_organization(organization_id)
        team = Team(organization_id=organization_id, department_id=department_id, name=name, lead_id=lead_id)
        self._store.teams.save(team.team_id, team)
        return team

    def create_project(
        self,
        organization_id: str,
        name: str,
        *,
        workspace_id: str = "",
        team_id: str = "",
    ) -> Project:
        self.get_organization(organization_id)
        project = Project(organization_id=organization_id, workspace_id=workspace_id, team_id=team_id, name=name)
        self._store.projects.save(project.project_id, project)
        return project

    async def add_member(
        self,
        organization_id: str,
        user_id: str,
        role_id: str,
        *,
        department_id: str = "",
        team_id: str = "",
    ) -> Membership:
        self.get_organization(organization_id)
        membership = Membership(
            organization_id=organization_id,
            user_id=user_id,
            role_id=role_id,
            department_id=department_id,
            team_id=team_id,
        )
        self._store.memberships.save(membership.membership_id, membership)
        role = self._permissions.get_role(role_id)
        await self._permissions.assign_role(user_id=user_id, role_id=role_id, organization_id=organization_id)
        return membership

    def create_invitation(
        self,
        organization_id: str,
        email: str,
        role_id: str,
        invited_by: str,
    ) -> Invitation:
        self.get_organization(organization_id)
        invitation = Invitation(
            organization_id=organization_id,
            email=email,
            role_id=role_id,
            invited_by=invited_by,
            token=secrets.token_urlsafe(24),
        )
        self._store.invitations.save(invitation.invitation_id, invitation)
        return invitation

    def accept_invitation(self, token: str, user_id: str) -> Membership:
        invitation = next((i for i in self._store.invitations.list_all() if i.token == token and i.status == "pending"), None)
        if invitation is None:
            raise ValidationError("Invalid or expired invitation")
        invitation.status = "accepted"
        self._store.invitations.save(invitation.invitation_id, invitation)
        membership = Membership(
            organization_id=invitation.organization_id,
            user_id=user_id,
            role_id=invitation.role_id,
        )
        self._store.memberships.save(membership.membership_id, membership)
        return membership

    def get_organization(self, organization_id: str) -> Organization:
        org = self._store.organizations.get(organization_id)
        if org is None:
            raise NotFoundError("Organization", organization_id)
        return org

    def list_organizations(self, *, owner_id: str = "") -> list[Organization]:
        orgs = self._store.organizations.list_all()
        if owner_id:
            return [o for o in orgs if o.owner_id == owner_id]
        return orgs

    def list_workspaces(self, organization_id: str) -> list[Workspace]:
        return [w for w in self._store.workspaces.list_all() if w.organization_id == organization_id]

    def list_members(self, organization_id: str) -> list[Membership]:
        return [m for m in self._store.memberships.list_all() if m.organization_id == organization_id]


organization_service = OrganizationService()
