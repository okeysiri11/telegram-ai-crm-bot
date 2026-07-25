"""Identity Center constants — Sprint 26.3."""

from __future__ import annotations

AUTH_PATH = "src/web/auth"
VERSION = "9.0.4"

ARCHITECTURE = (
    "authentication_ui",
    "identity_manager",
    "organization_manager",
    "user_manager",
    "role_manager",
    "permission_manager",
    "session_manager",
    "mfa_center",
    "security_center",
    "profile_center",
    "activity_center",
    "authentication_dashboard",
)

AUTH_PAGES = (
    "login",
    "logout",
    "forgot_password",
    "reset_password",
    "change_password",
    "account_locked",
    "session_expired",
    "access_denied",
)

LOGIN_FEATURES = (
    "email",
    "username",
    "password",
    "remember_me",
    "tenant_selection",
    "language_selection",
    "workspace_restore",
    "last_page_restore",
    "preferences_load",
)

MFA_METHODS = ("totp", "email_code", "backup_codes")
MFA_EXTENSIONS = ("fido2", "webauthn", "hardware_security_keys")

ORG_KINDS = ("companies", "departments", "teams", "branches", "projects")

USER_ACTIONS = (
    "create_user",
    "edit_user",
    "disable_user",
    "delete_user",
    "invite_user",
    "import_users",
    "export_users",
)

ROLE_SCOPES = ("system", "organization", "project", "custom")
PERMISSION_DOMAINS = (
    "crm",
    "erp",
    "ai_agents",
    "finance",
    "hr",
    "analytics",
    "marketplace",
    "administration",
    "api_access",
)

SESSION_ACTIONS = ("logout_current", "logout_all", "session_revocation")

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "design_system",
    "web_foundation",
    "ai_orchestrator",
    "workflow_engine",
    "notification_center",
    "security_platform",
    "audit_platform",
    "authentication_api",
    "identity_service",
    "rbac_platform",
    "monitoring_platform",
)

KPI_TARGETS = {
    "authentication_ui_ready": True,
    "identity_center_ready": True,
    "organization_management": True,
    "user_management": True,
    "role_management": True,
    "permission_management": True,
    "mfa_ready": True,
    "session_management": True,
    "security_center_ready": True,
    "profile_center_ready": True,
    "enterprise_core_integrated": True,
}

PRINCIPLES = (
    "secure_auth_ui",
    "identity_center_unified",
    "design_system_forms",
    "rbac_synced_permissions",
    "mfa_first",
    "phase3_identity_center",
)
