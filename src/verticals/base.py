# Vertical definition — metadata for multi-vertical CRM routing.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerticalDefinition:
    code: str
    title: str
    domain_package: str
    legacy_service_prefix: str
    maturity: str  # production | partial | scaffold
    manager_role: str | None = None
    description: str = ""
    capabilities: tuple[str, ...] = field(default_factory=tuple)
