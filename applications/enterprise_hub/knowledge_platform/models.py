"""Knowledge Platform models — Sprint 20.3."""

from __future__ import annotations

DOC_TYPES = ("pdf", "docx", "xlsx", "pptx", "html", "markdown", "email", "image", "article", "policy")
DOC_STATUSES = ("draft", "active", "archived", "expired")
MEMORY_TIERS = (
    "short_term",
    "long_term",
    "project",
    "organization",
    "personal",
    "ai_shared",
)
ENTITY_KINDS = (
    "user",
    "company",
    "project",
    "contract",
    "task",
    "document",
    "ai_agent",
    "business_process",
)
CONNECTORS = (
    "filesystem",
    "google_drive",
    "onedrive",
    "sharepoint",
    "notion",
    "confluence",
    "github",
    "custom",
)
SEARCH_MODES = ("semantic", "keyword", "hybrid", "graph")
