"""Workspace kind helpers — CRM, ERP, Finance, AI, custom."""

from __future__ import annotations

from applications.enterprise_hub.tenancy.workspaces.ai import AIWorkspace
from applications.enterprise_hub.tenancy.workspaces.crm import CRMWorkspace
from applications.enterprise_hub.tenancy.workspaces.custom import CustomWorkspace
from applications.enterprise_hub.tenancy.workspaces.erp import ERPWorkspace
from applications.enterprise_hub.tenancy.workspaces.finance import FinanceWorkspace

__all__ = [
    "CRMWorkspace",
    "ERPWorkspace",
    "FinanceWorkspace",
    "AIWorkspace",
    "CustomWorkspace",
]
