"""ISAM models and constants — Sprint 19.8 / 30.1."""

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
    "google",
    "microsoft",
    "apple",
    "github",
    "telegram",
)

MFA_METHODS = ("totp", "email", "sms", "hardware_key", "backup_codes")

# Sprint 30.1 enterprise role catalog (additive — legacy roles retained)
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
    # Canonical enterprise roles
    "owner",
    "administrator",
    "client",
    "dealer",
    "partner",
    "accountant",
    "lawyer",
    "production",
    "viewer",
)

# Alias map: UI / product role → ISAM role id
ENTERPRISE_ROLE_ALIASES = {
    "Owner": "owner",
    "Administrator": "administrator",
    "Manager": "manager",
    "Employee": "employee",
    "Client": "client",
    "Dealer": "dealer",
    "Partner": "partner",
    "Accountant": "accountant",
    "Lawyer": "lawyer",
    "Production": "production",
    "Viewer": "viewer",
    "company_owner": "owner",
    "platform_admin": "administrator",
    "read_only": "viewer",
}

TOKEN_TYPES = ("access", "refresh", "api", "personal_access")

POLICY_KINDS = ("ip", "time", "geo", "device", "role", "company", "mfa_required")

AUDIT_ACTIONS = (
    "login",
    "logout",
    "login_failed",
    "google_login",
    "password_reset",
    "password_change",
    "email_verification",
    "mfa_enable",
    "mfa_disable",
    "mfa_challenge",
    "permission_change",
    "role_change",
    "profile_change",
    "session_revoke",
    "session_revoke_all",
    "api_access",
    "authorization",
    "register",
)
