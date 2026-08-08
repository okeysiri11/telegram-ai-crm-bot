"""Sprint 46.1 — Telegram tenant session (never expose raw tenant errors to clients)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID

from services.auto_client_output import user_facing_tenant_error_ru
from services.tenant_context import TenantContextService


@dataclass
class TelegramTenantSession:
    tenant_id: str
    organization_id: str
    workspace_id: str
    user_role: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# In-memory session cache for Telegram users
_sessions: dict[int, TelegramTenantSession] = {}
_pending_choice: dict[int, list[dict[str, str]]] = {}


def get_cached_session(user_id: int) -> TelegramTenantSession | None:
    return _sessions.get(user_id)


def save_session(user_id: int, session: TelegramTenantSession) -> None:
    _sessions[user_id] = session
    try:
        TenantContextService.set_active_tenant(user_id, UUID(session.tenant_id))
    except Exception:
        pass


def clear_session(user_id: int) -> None:
    _sessions.pop(user_id, None)
    _pending_choice.pop(user_id, None)
    TenantContextService.clear_active_tenant(user_id)


async def ensure_telegram_tenant_session(user_id: int) -> dict[str, Any]:
    """
    Resolve tenant for Telegram.

    Returns:
      {"ok": True, "session": TelegramTenantSession}
      {"ok": False, "needs_choice": True, "options": [...], "message_ru": "..."}
      {"ok": False, "message_ru": "..."}
    """
    cached = get_cached_session(user_id)
    if cached:
        return {"ok": True, "session": cached}

    try:
        ctx = await TenantContextService.resolve_for_user(user_id)
    except Exception:
        return {"ok": False, "message_ru": user_facing_tenant_error_ru()}

    if ctx is not None:
        session = TelegramTenantSession(
            tenant_id=str(ctx.tenant_id),
            organization_id=str(ctx.company_id),
            workspace_id=str(ctx.tenant_id),
            user_role=ctx.role_code or "client",
        )
        save_session(user_id, session)
        return {"ok": True, "session": session}

    # Multiple bindings / no binding — try list
    try:
        tenant_ids = await TenantContextService.list_user_tenant_ids(user_id)
    except Exception:
        tenant_ids = []

    if len(tenant_ids) > 1:
        options = [
            {
                "tenant_id": str(tid),
                "organization_id": str(tid),
                "workspace_id": str(tid),
                "label": f"Организация {i + 1}",
            }
            for i, tid in enumerate(tenant_ids)
        ]
        _pending_choice[user_id] = options
        return {
            "ok": False,
            "needs_choice": True,
            "options": options,
            "message_ru": user_facing_tenant_error_ru(),
        }

    if len(tenant_ids) == 1:
        tid = tenant_ids[0]
        session = TelegramTenantSession(
            tenant_id=str(tid),
            organization_id=str(tid),
            workspace_id=str(tid),
            user_role="member",
        )
        save_session(user_id, session)
        return {"ok": True, "session": session}

    return {"ok": False, "message_ru": user_facing_tenant_error_ru()}


async def select_workspace(user_id: int, tenant_id: str) -> TelegramTenantSession | None:
    options = _pending_choice.get(user_id) or []
    match = next((o for o in options if o["tenant_id"] == tenant_id), None)
    if match is None:
        try:
            UUID(tenant_id)
        except Exception:
            return None
        match = {
            "tenant_id": tenant_id,
            "organization_id": tenant_id,
            "workspace_id": tenant_id,
        }
    session = TelegramTenantSession(
        tenant_id=match["tenant_id"],
        organization_id=match.get("organization_id") or match["tenant_id"],
        workspace_id=match.get("workspace_id") or match["tenant_id"],
        user_role="member",
    )
    save_session(user_id, session)
    _pending_choice.pop(user_id, None)
    return session
