"""Integration façade — domains call Hercules instead of ad-hoc runtimes."""

from __future__ import annotations

from typing import Any

from platform_hercules.core.models import ExecutionContext
from platform_hercules.runtime.hercules_runtime import hercules_runtime


DOMAIN_CHANNELS = {
    "crm": "crm",
    "erp": "erp",
    "ai_studio": "ai_studio",
    "beauty": "beauty",
    "auto": "auto",
    "crypto": "crypto",
    "agro": "agro",
    "drone": "drone",
    "construction": "construction",
    "production": "production",
    "knowledge": "knowledge",
    "marketplace": "marketplace",
    "telegram": "telegram",
    "owner": "desktop",
    "agents": "agent",
    "workflow_studio": "workflow",
    "production_studio": "workflow",
}


async def run_via_hercules(
    domain: str,
    *,
    owner_id: str,
    prompt: str,
    modality: str = "text",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical entry — all listed domains should prefer this path."""
    channel = DOMAIN_CHANNELS.get(domain, "internal")
    job = await hercules_runtime.submit_ai(
        ExecutionContext(
            owner_id=owner_id,
            channel=channel,
            vertical=domain if domain in ("beauty", "auto", "crypto", "agro") else None,
            meta=meta or {},
        ),
        prompt=prompt,
        modality=modality,
        vertical=domain if domain in ("beauty", "auto", "crypto", "agro") else None,
    )
    return hercules_runtime.status(job.id) or {"id": job.id}


def bridge_telegram_ai_to_hercules() -> None:
    """Soft note — Telegram Super App continues via UnifiedAiPipeline;
    Owner Hercules commands use hercules_runtime directly."""
    return None
