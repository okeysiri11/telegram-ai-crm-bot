# DashboardService — manager dashboard operations via RequestService.

from __future__ import annotations

import uuid
from typing import Any

from services.request_service import request_service


class DashboardService:
    @staticmethod
    async def get_new_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return await request_service.get_new_requests(manager_id, limit=limit)

    @staticmethod
    async def get_active_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return await request_service.get_active_requests(manager_id, limit=limit)

    @staticmethod
    async def get_overdue_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return await request_service.get_overdue_requests(manager_id, limit=limit)

    @staticmethod
    async def get_completed_requests(
        manager_id: uuid.UUID | str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return await request_service.get_completed_requests(manager_id, limit=limit)

    @staticmethod
    async def take_request(
        request_id: str,
        manager_id: uuid.UUID | str,
    ) -> dict[str, Any] | None:
        return await request_service.take_request(request_id, manager_id)

    @staticmethod
    async def complete_request(request_id: str) -> dict[str, Any] | None:
        return await request_service.complete_request(request_id)

    @staticmethod
    async def reassign_request(
        request_id: str,
        manager_id: uuid.UUID | str,
    ) -> dict[str, Any] | None:
        return await request_service.reassign_request(request_id, manager_id)

    @staticmethod
    def format_request_lines(title: str, requests: list[dict[str, Any]]) -> str:
        if not requests:
            return f"{title}\n\nНет заявок."
        lines = [title, ""]
        for idx, req in enumerate(requests, 1):
            desc = (req.get("description") or "")[:80]
            lines.append(
                f"{idx}. #{req.get('request_number')} | {req.get('status')}\n"
                f"   {req.get('vertical', '').upper()} · {req.get('request_type')}\n"
                f"   {desc or '—'}"
            )
        return "\n".join(lines)


dashboard_service = DashboardService()
