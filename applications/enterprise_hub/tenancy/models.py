"""Tenancy models and constants — Sprint 20.0."""

from __future__ import annotations

LICENSE_TIERS = (
    "free",
    "startup",
    "business",
    "enterprise",
    "government",
    "custom",
)

ORG_LEVELS = (
    "holding",
    "company",
    "branch",
    "department",
    "team",
    "employee",
)

WORKSPACE_KINDS = ("crm", "erp", "finance", "ai", "custom", "documents")

ISOLATION_SCOPES = (
    "data",
    "files",
    "ai_context",
    "api",
    "queues",
    "logs",
    "backups",
)

ENVIRONMENTS = ("production", "staging", "development", "sandbox")

BRANDING_KEYS = (
    "logo",
    "colors",
    "domain",
    "theme",
    "language",
    "timezone",
    "currency",
    "locale",
)

BILLING_STATUSES = ("active", "past_due", "canceled", "trialing")
SUBSCRIPTION_STATUSES = ("active", "paused", "canceled", "trial")
