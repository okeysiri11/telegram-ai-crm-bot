# Sprint 34.2A — Canonical workspace / vertical registry.
#
# Switching workspace preserves the same users.id identity.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceDefinition:
    code: str
    label: str
    description: str
    # Route hints for clients (renderers only — not separate backends).
    web_path: str | None = None
    telegram_entry: str | None = None


WORKSPACE_REGISTRY: dict[str, WorkspaceDefinition] = {
    "company_core": WorkspaceDefinition(
        "company_core",
        "Company Core",
        "HR, departments, KPI",
        web_path="/workspace/company-core",
        telegram_entry="company_core",
    ),
    "crypto_otc": WorkspaceDefinition(
        "crypto_otc",
        "Crypto OTC",
        "OTC trading vertical",
        web_path="/workspace/crypto",
        telegram_entry="crypto",
    ),
    "drone": WorkspaceDefinition(
        "drone",
        "Drone Engineering",
        "Drone engineering vertical",
        web_path="/workspace/drone",
        telegram_entry="drone",
    ),
    "agro": WorkspaceDefinition(
        "agro",
        "Agro Trading",
        "Agriculture trading vertical",
        web_path="/workspace/agro",
        telegram_entry="agro",
    ),
    "cafe_beauty": WorkspaceDefinition(
        "cafe_beauty",
        "Cafe & Beauty",
        "Hospitality and beauty verticals",
        web_path="/workspace/cafe",
        telegram_entry="cafe_beauty",
    ),
    "auto": WorkspaceDefinition(
        "auto",
        "Automotive",
        "Auto marketplace and CRM",
        web_path="/workspace/auto",
        telegram_entry="auto_client",
    ),
    "legal": WorkspaceDefinition(
        "legal",
        "Legal",
        "Legal enterprise vertical",
        web_path="/workspace/legal",
        telegram_entry="legal",
    ),
    "construction": WorkspaceDefinition(
        "construction",
        "Construction",
        "Construction vertical (SPEC → live)",
        web_path="/workspace/construction",
        telegram_entry=None,
    ),
    "manufacturing": WorkspaceDefinition(
        "manufacturing",
        "Manufacturing",
        "Manufacturing / production ERP view",
        web_path="/erp?view=production",
        telegram_entry=None,
    ),
    "medical": WorkspaceDefinition(
        "medical",
        "Medical",
        "Medical vertical (SPEC → live)",
        web_path="/workspace/medical",
        telegram_entry=None,
    ),
}


def all_workspaces() -> list[WorkspaceDefinition]:
    return list(WORKSPACE_REGISTRY.values())


def workspace_by_code(code: str | None) -> WorkspaceDefinition | None:
    if not code:
        return None
    return WORKSPACE_REGISTRY.get(str(code).strip().lower())


def normalize_workspace_codes(raw: list[str] | tuple[str, ...] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in raw or []:
        key = str(item).strip().lower()
        # Map common vertical aliases
        aliases = {
            "crypto": "crypto_otc",
            "beauty": "cafe_beauty",
            "cafe": "cafe_beauty",
            "automotive": "auto",
            "company-core": "company_core",
            "company": "company_core",
        }
        code = aliases.get(key, key)
        if code in WORKSPACE_REGISTRY and code not in seen:
            seen.add(code)
            out.append(code)
    return out
