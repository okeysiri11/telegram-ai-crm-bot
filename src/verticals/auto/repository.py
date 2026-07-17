# Auto vertical repository — wraps legacy auto_client_request repository.

from __future__ import annotations

from repositories.auto_client_request_repository import AutoClientRequestRepository
from src.platform.layers.base_repository import BaseRepository


class AutoVerticalRepository(BaseRepository):
    """Auto-specific persistence. Prefer AutoVerticalService for handlers."""

    def auto_client_requests(self) -> AutoClientRequestRepository:
        return AutoClientRequestRepository(self.session)
