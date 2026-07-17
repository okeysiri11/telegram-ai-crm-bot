# Agro vertical repository — pipeline boards and lead persistence.

from __future__ import annotations

from repositories.crm_pipeline_boards_repository import CrmPipelineBoardsRepository
from src.platform.layers.base_repository import BaseRepository


class AgroVerticalRepository(BaseRepository):
    def pipeline_boards(self) -> CrmPipelineBoardsRepository:
        return CrmPipelineBoardsRepository(self.session)
