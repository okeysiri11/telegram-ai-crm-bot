# Crop AI — crop advice using knowledge + harvest context.

from __future__ import annotations

from typing import Any

from applications.agro_marketplace.ai.knowledge import AgroKnowledgeService, agro_knowledge
from applications.agro_marketplace.agents.service import AgroAgentService, agent_service
from applications.agro_marketplace.ai.models import AgroAgentType
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class CropAIService:
    def __init__(
        self,
        store: AgroStore | None = None,
        knowledge: AgroKnowledgeService | None = None,
        agents: AgroAgentService | None = None,
    ) -> None:
        self._store = store or agro_store
        self._knowledge = knowledge or agro_knowledge
        self._agents = agents or agent_service

    def advise(self, crop: str, *, region: str = "") -> dict[str, Any]:
        taxonomy = self._knowledge.search(crop)
        seasonality = self._knowledge.seasonality(crop=crop, region=region)
        harvests = [
            h.to_dict()
            for h in self._store.harvest_records.list_all()
            if h.crop_id.lower() == crop.lower()
            and (not region or h.region.lower() == region.lower())
        ]
        return {
            "crop": crop,
            "region": region,
            "knowledge": taxonomy[:5],
            "seasonality": seasonality,
            "recent_harvests": harvests[:5],
            "tips": [
                "Monitor moisture before storage",
                "Align planting with seasonality windows",
                "Use graded lots for premium pricing",
            ],
        }

    async def ask(self, message: str, *, user_id: str = "", crop: str = "") -> dict[str, Any]:
        context = self.advise(crop) if crop else {}
        invocation = await self._agents.invoke(
            AgroAgentType.CROP_ADVISOR,
            message,
            user_id=user_id,
            context=context,
        )
        return invocation.to_dict()


crop_ai_service = CropAIService()
