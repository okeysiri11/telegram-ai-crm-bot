"""Security hardening constants — Sprint 21.4."""

from __future__ import annotations

AUTH_METHODS = (
    "oauth2",
    "oidc",
    "jwt",
    "refresh_token",
    "service_account",
    "api_key",
    "mfa",
)

ABAC_ATTRIBUTES = (
    "organization",
    "department",
    "project",
    "owner",
    "secrecy_level",
    "geo_zone",
    "operation_type",
)

ZERO_TRUST_CHECKS = (
    "user",
    "device",
    "token",
    "ip",
    "context",
    "risk_level",
    "security_policy",
)

SECRET_KINDS = (
    "api_key",
    "jwt_secret",
    "encryption_key",
    "database_password",
    "cloud_credential",
    "ai_provider_key",
)

ENCRYPTION_ALGORITHMS = (
    "tls_1_3",
    "aes_256",
    "rsa",
    "ed25519",
    "hashing",
    "digital_signature",
)

AUDIT_ACTIONS = (
    "user_login",
    "ai_action",
    "data_change",
    "role_change",
    "workflow_start",
    "api_access",
    "admin_action",
)

MONITORING_SIGNALS = (
    "password_spray",
    "anomalous_request",
    "suspicious_token",
    "unusual_activity",
    "mass_delete",
    "data_exfiltration",
)

PROTECTION_CONTROLS = (
    "rate_limit",
    "burst_control",
    "api_quota",
    "anti_bruteforce",
    "anti_ddos",
    "request_validation",
)

COMPLIANCE_FRAMEWORKS = (
    "gdpr",
    "iso_27001",
    "soc_2",
    "nist_csf",
    "owasp_asvs",
)

SECURITY_TESTS = (
    "dependency_scan",
    "secret_scan",
    "sast",
    "dast",
    "container_scan",
    "license_audit",
    "security_regression",
)

INTEGRATION_TARGETS = (
    "api_platform",
    "ai_agents",
    "workflow",
    "event_bus",
    "data_fabric",
    "enterprise_hub",
    "vertical_modules",
)
