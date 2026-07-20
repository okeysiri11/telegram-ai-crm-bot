# Platform Security Layer.

from platform_security.audit import AuditManager, audit_manager
from platform_security.authentication import AuthenticationProvider, OAuthProvider, authentication_provider
from platform_security.authorization import AuthorizationManager, authorization_manager
from platform_security.config import DEFAULT_SECURITY_CONFIG, SecurityConfig
from platform_security.integrations import SecurityIntegrations, security_integrations
from platform_security.models import (
    AccessPolicy,
    AuditEventType,
    AuditRecord,
    AuthMethodType,
    PermissionScope,
    SecretRecord,
    SecurityPrincipal,
    SecurityRole,
)
from platform_security.permissions import PermissionManager, permission_manager
from platform_security.roles import RoleManager, role_manager
from platform_security.secrets import SecretManager, secret_manager
from platform_security.security_manager import SecurityManager, security_manager
from platform_security.sessions import SessionManager, session_manager

__all__ = [
    "DEFAULT_SECURITY_CONFIG",
    "AccessPolicy",
    "AuditEventType",
    "AuditManager",
    "AuditRecord",
    "AuthMethodType",
    "AuthenticationProvider",
    "AuthorizationManager",
    "OAuthProvider",
    "PermissionManager",
    "PermissionScope",
    "RoleManager",
    "SecretManager",
    "SecretRecord",
    "SecurityConfig",
    "SecurityIntegrations",
    "SecurityManager",
    "SecurityPrincipal",
    "SecurityRole",
    "SessionManager",
    "audit_manager",
    "authentication_provider",
    "authorization_manager",
    "permission_manager",
    "role_manager",
    "secret_manager",
    "security_integrations",
    "security_manager",
    "session_manager",
]
