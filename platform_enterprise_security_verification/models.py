"""Security Verification constants — Sprint 25.5."""

from __future__ import annotations

AUTHN_CHECKS = (
    "jwt",
    "oauth2",
    "api_keys",
    "refresh_tokens",
    "session_validation",
    "mfa_support",
    "token_expiration",
    "token_revocation",
)

AUTHZ_CHECKS = (
    "rbac",
    "role_hierarchy",
    "permission_matrix",
    "resource_access",
    "tenant_isolation",
    "admin_permissions",
    "ai_permissions",
)

TENANT_ISOLATION_CHECKS = (
    "companies",
    "users",
    "documents",
    "ai_memory",
    "workflows",
    "files",
    "logs",
)

API_SECURITY_CHECKS = (
    "authentication_required",
    "authorization_required",
    "rate_limiting",
    "input_validation",
    "output_validation",
    "injection_protection",
    "error_handling",
    "security_headers",
)

VULN_CHECKS = (
    "sql_injection",
    "nosql_injection",
    "xss",
    "csrf",
    "ssrf",
    "path_traversal",
    "command_injection",
    "xxe",
    "open_redirect",
    "file_upload_validation",
)

SECRET_PATTERNS = (
    "api_keys",
    "tokens",
    "passwords",
    "private_keys",
    "certificates",
    "environment_secrets",
    "database_credentials",
)

DEPENDENCY_SOURCES = (
    "python_packages",
    "node_packages",
    "docker_images",
    "base_images",
    "third_party_libraries",
)

AUDIT_EVENTS = (
    "login",
    "logout",
    "permission_changes",
    "role_changes",
    "security_events",
    "failed_authentication",
    "failed_authorization",
    "configuration_changes",
)

COMPLIANCE_FRAMEWORKS = (
    "iso_27001",
    "soc_2",
    "gdpr",
    "owasp_top_10",
    "cis_benchmarks",
)

REPORT_KINDS = (
    "security",
    "vulnerability",
    "dependency",
    "compliance",
    "audit",
    "executive_summary",
)

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "enterprise_ai_orchestrator",
    "observability",
    "chaos_engineering",
    "performance_testing",
    "migration",
    "communications",
    "test_infrastructure",
)

KPI_TARGETS = {
    "centralized_security_checks": True,
    "auto_vulnerability_detection": True,
    "dependency_scanning": True,
    "secret_control": True,
    "security_audit": True,
    "security_dashboard": True,
    "auto_security_reports": True,
    "block_release_on_critical": True,
    "no_duplicated_esh_logic": True,
}

PRINCIPLES = (
    "verify_never_exploit",
    "centralized_security_gate",
    "block_critical_before_production",
    "additive_to_esh_isam",
    "no_duplicated_business_logic",
)
