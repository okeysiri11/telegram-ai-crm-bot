"""EDP models and constants — Sprint 19.7."""

from __future__ import annotations

ENTITY_TYPES = (
    "user",
    "company",
    "contact",
    "customer",
    "supplier",
    "project",
    "product",
    "service",
    "asset",
    "equipment",
    "document",
    "financial_object",
    "location",
)

MASTER_DOMAINS = (
    "users",
    "companies",
    "customers",
    "suppliers",
    "projects",
    "products",
    "services",
    "equipment",
    "documents",
    "financial_objects",
)

CLASSIFICATIONS = ("public", "internal", "confidential", "restricted")

QUALITY_CHECKS = (
    "duplicate",
    "null",
    "contradiction",
    "format",
    "stale",
    "business_rule",
)
