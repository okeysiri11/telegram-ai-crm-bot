"""ISAM models and constants — Sprint 19.8."""

from __future__ import annotations

IDENTITY_TYPES = ("user", "service_account", "ai_agent", "external_system")

AUTH_METHODS = (
    "password",
    "jwt",
    "oauth2",
    "oidc",
    "ldap",
    "active_directory",
    "api_key",
    "service_account",
)

MFA_METHODS = ("totp", "email", "sms", "hardware_key", "backup_codes")

ROLES = (
    "super_admin",
    "platform_admin",
    "company_owner",
    "manager",
    "employee",
    "auditor",
    "ai_agent",
    "integration_service",
    "read_only",
)

TOKEN_TYPES = ("access", "refresh", "api", "personal_access")

POLICY_KINDS = ("ip", "time", "geo", "device", "role", "company")
