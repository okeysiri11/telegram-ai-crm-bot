# Secret policy — Sprint 32.3.
# No placeholder secrets may satisfy production (or CI secret scan).

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platform_security.jwt_secrets import insecure_secret_set, is_insecure_secret

# Extended insecure / placeholder vocabulary (JWT set + infra placeholders).
_EXTRA_INSECURE = frozenset(
    {
        "change-me-ados-n8n-key",
        "change-me",
        "changeme",
        "secret",
        "password",
        "postgres",
        "platform-dev-key",
        "dev-secret",
        "test-secret",
        "your-api-key-here",
        "sk-placeholder",
        "REPLACE_ME",
    }
)

REQUIRED_PRODUCTION_SECRETS = (
    "IAM_JWT_SECRET",
    "JWT_SECRET",
    "API_JWT_SECRET",
    "SECURITY_MASTER_KEY",
    "DATABASE_URL",
    "REDIS_URL",
)

OPTIONAL_PROVIDER_SECRETS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "SMTP_PASSWORD",
    "S3_SECRET_KEY",
    "N8N_ENCRYPTION_KEY",
    "MCP_API_KEY",
)

# Patterns that must not appear as compose/env defaults in production files.
INSECURE_DEFAULT_PATTERNS = (
    re.compile(r"change-me", re.I),
    re.compile(r"N8N_ENCRYPTION_KEY:\$\{N8N_ENCRYPTION_KEY:-[^}]+\}"),
    re.compile(r'getenv\(\s*["\']API_JWT_SECRET["\']\s*,\s*["\']change-me'),
    re.compile(r'getenv\(\s*["\']JWT_SECRET["\']\s*,\s*["\']change-me'),
)


@dataclass
class SecretFinding:
    code: str
    severity: str
    message: str
    path: str | None = None


@dataclass
class SecretPolicyReport:
    passed: bool
    findings: list[SecretFinding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "findings": [f.__dict__ for f in self.findings],
        }


def all_insecure_values() -> frozenset[str]:
    return frozenset(set(insecure_secret_set()) | set(_EXTRA_INSECURE))


def is_forbidden_secret(value: str | None) -> bool:
    if value is None or not str(value).strip():
        return True
    v = str(value).strip()
    if is_insecure_secret(v):
        return True
    if v.lower() in {x.lower() for x in _EXTRA_INSECURE}:
        return True
    return False


def validate_runtime_secrets(*, production: bool | None = None) -> SecretPolicyReport:
    """Validate process env against secret policy."""
    env = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "development").lower()
    is_prod = production if production is not None else env in {"production", "prod", "staging"}
    findings: list[SecretFinding] = []

    for name in REQUIRED_PRODUCTION_SECRETS:
        value = os.getenv(name)
        if is_prod and is_forbidden_secret(value):
            findings.append(
                SecretFinding(
                    code="SECRET_REQUIRED",
                    severity="critical",
                    message=f"{name} must be set to a non-placeholder value in production",
                )
            )
        elif not is_prod and is_forbidden_secret(value):
            findings.append(
                SecretFinding(
                    code="SECRET_DEV_PLACEHOLDER",
                    severity="info",
                    message=f"{name} is unset/placeholder (allowed in non-production)",
                )
            )

    for name in OPTIONAL_PROVIDER_SECRETS:
        value = os.getenv(name)
        if value and is_forbidden_secret(value):
            findings.append(
                SecretFinding(
                    code="SECRET_PLACEHOLDER_SET",
                    severity="critical" if is_prod else "warn",
                    message=f"{name} is set to a known placeholder — remove or replace",
                )
            )

    critical = [f for f in findings if f.severity == "critical"]
    return SecretPolicyReport(passed=len(critical) == 0, findings=findings)


def scan_repo_for_insecure_defaults(root: Path | None = None) -> SecretPolicyReport:
    """Static scan of compose/config for insecure default patterns (Sprint 32.3 gate)."""
    if root is None:
        from platform_architecture.rules import ROOT

        root = ROOT
    findings: list[SecretFinding] = []
    targets = [
        root / "docker-compose.n8n.yml",
        root / "docker-compose.yml",
        root / "docker-compose.prod.yml",
        root / "platform_configuration" / "configuration_center.py",
        root / "platform_configuration" / "settings.py",
    ]
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = str(path.relative_to(root))
        # N8N must not ship with inline default encryption key.
        if path.name == "docker-compose.n8n.yml":
            if "change-me-ados-n8n-key" in text or re.search(
                r"N8N_ENCRYPTION_KEY:\s*\$\{N8N_ENCRYPTION_KEY:-[^}]+\}", text
            ):
                findings.append(
                    SecretFinding(
                        code="N8N_INSECURE_DEFAULT",
                        severity="critical",
                        message="N8N_ENCRYPTION_KEY must not use an insecure compose default",
                        path=rel,
                    )
                )
            elif "N8N_ENCRYPTION_KEY" in text:
                findings.append(
                    SecretFinding(
                        code="N8N_KEY_OK",
                        severity="info",
                        message="N8N_ENCRYPTION_KEY requires explicit env (no insecure default)",
                        path=rel,
                    )
                )
        # Flag remaining change-me getenv defaults in settings (warn — load-time defaults still
        # exist for local boot but production validate must fail).
        if "change-me-in-production" in text and "settings.py" in rel:
            findings.append(
                SecretFinding(
                    code="SETTINGS_DEFAULT_PLACEHOLDER",
                    severity="warn",
                    message="Pydantic settings still declare placeholder defaults — production validate must reject",
                    path=rel,
                )
            )

    critical = [f for f in findings if f.severity == "critical"]
    return SecretPolicyReport(passed=len(critical) == 0, findings=findings)


def secret_policy_summary() -> dict[str, Any]:
    return {
        "required_production": list(REQUIRED_PRODUCTION_SECRETS),
        "optional_providers": list(OPTIONAL_PROVIDER_SECRETS),
        "insecure_vocabulary_size": len(all_insecure_values()),
        "sprint": "32.3",
    }
