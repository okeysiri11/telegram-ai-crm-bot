# Logistics vertical repository — scaffold.

from __future__ import annotations

from repositories.client_request_repository import ClientRequestRepository
from src.platform.layers.base_repository import BaseRepository


class LogisticsVerticalRepository(BaseRepository):
    def client_requests(self) -> ClientRequestRepository:
        return ClientRequestRepository(self.session)
