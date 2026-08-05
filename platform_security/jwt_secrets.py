"""Canonical JWT secret resolution — Sprint 30.0 (TD-57).

All signing/verification paths must use ``resolve_iam_signing_secret()``.
``PlatformSettings.jwt.secret`` and ``jwt.iam_secret`` are normalized at load time
so the unvalidated getenv default cannot silently diverge from IAM validation.
"""

from __future__ import annotations

_INSECURE_JWT_SECRETS = frozenset(
    {
        "",
        "change-me-in-production",
        "change-me-in-production-api-jwt-secret",
        "change-me-ados-n8n-key",
        "change-me",
        "changeme",
        "dev-secret",
        "test-secret",
        "platform-dev-key",
    }
)


def is_insecure_secret(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip() in _INSECURE_JWT_SECRETS


def normalize_jwt_secrets(*, jwt_secret: str, iam_secret: str) -> tuple[str, str]:
    """Prefer IAM_JWT_SECRET; fall back to JWT_SECRET; keep both in sync when one is set."""
    jwt_secret = (jwt_secret or "").strip()
    iam_secret = (iam_secret or "").strip()
    if not is_insecure_secret(iam_secret):
        # Authoritative IAM secret — mirror onto legacy JWT_SECRET when insecure
        if is_insecure_secret(jwt_secret):
            jwt_secret = iam_secret
        return jwt_secret, iam_secret
    if not is_insecure_secret(jwt_secret):
        return jwt_secret, jwt_secret
    return jwt_secret or "change-me-in-production", iam_secret or jwt_secret or "change-me-in-production"


def resolve_iam_signing_secret() -> str:
    """Single source of truth for IAM access/refresh token HMAC key."""
    from platform_configuration.configuration_center import configuration_center

    jwt = configuration_center.settings.jwt
    secret = (jwt.iam_secret or jwt.secret or "").strip()
    return secret


def validate_signing_secret(secret: str | None = None) -> None:
    value = (secret if secret is not None else resolve_iam_signing_secret()).strip()
    if is_insecure_secret(value):
        raise RuntimeError(
            "IAM_JWT_SECRET must be set to a secure value "
            "(not empty and not 'change-me-in-production')"
        )


def insecure_secret_set() -> frozenset[str]:
    return _INSECURE_JWT_SECRETS
