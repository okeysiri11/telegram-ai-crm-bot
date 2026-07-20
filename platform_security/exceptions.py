# Security layer exceptions.

from __future__ import annotations


class SecurityError(Exception):
    def __init__(self, message: str, *, code: str = "security_error") -> None:
        super().__init__(message)
        self.code = code


class AuthenticationFailedError(SecurityError):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="authentication_failed")


class AuthorizationDeniedError(SecurityError):
    def __init__(self, message: str = "Authorization denied", *, permission: str = "") -> None:
        super().__init__(message, code="authorization_denied")
        self.permission = permission


class SecretNotFoundError(SecurityError):
    def __init__(self, secret_id: str) -> None:
        super().__init__(f"Secret not found: {secret_id}", code="secret_not_found")
        self.secret_id = secret_id


class SessionInvalidError(SecurityError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Invalid session: {session_id}", code="session_invalid")


class PolicyViolationError(SecurityError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="policy_violation")
