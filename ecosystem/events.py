# Ecosystem events — Sprint 7.1.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class UserLoggedInEvent(BaseEvent):
    user_id: str = ""
    session_id: str = ""
    organization_id: str = ""
    device_id: str = ""


@dataclass(kw_only=True)
class WorkspaceCreatedEvent(BaseEvent):
    workspace_id: str = ""
    organization_id: str = ""
    owner_id: str = ""


@dataclass(kw_only=True)
class OrganizationCreatedEvent(BaseEvent):
    organization_id: str = ""
    owner_id: str = ""
    tenant_id: str = ""


@dataclass(kw_only=True)
class RoleAssignedEvent(BaseEvent):
    user_id: str = ""
    role_id: str = ""
    role_name: str = ""
    organization_id: str = ""


@dataclass(kw_only=True)
class ApplicationOpenedEvent(BaseEvent):
    user_id: str = ""
    application_id: str = ""
    workspace_id: str = ""


@dataclass(kw_only=True)
class AssistantInvokedEvent(BaseEvent):
    user_id: str = ""
    session_id: str = ""
    application_id: str = ""
    intent: str = ""
