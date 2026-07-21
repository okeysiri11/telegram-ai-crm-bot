# Feedback ingestion facade.

from __future__ import annotations

from ecosystem.optimization.continuous_learning.service import ContinuousLearningService, continuous_learning
from ecosystem.optimization.models import FeedbackItem
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class FeedbackService:
    def __init__(
        self,
        store: EcosystemStore | None = None,
        learning: ContinuousLearningService | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self.learning = learning or continuous_learning

    def submit(
        self,
        rating: float,
        comment: str = "",
        *,
        source: str = "user",
        target_type: str = "workflow",
        target_id: str = "",
        tags: list[str] | None = None,
    ) -> FeedbackItem:
        return self.learning.ingest_feedback(
            source=source,
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            comment=comment,
            tags=tags,
        )

    def list_all(self) -> list[FeedbackItem]:
        return sorted(self._store.feedback_items.list_all(), key=lambda f: f.created_at, reverse=True)

    def average_rating(self) -> float:
        items = self._store.feedback_items.list_all()
        if not items:
            return 0.0
        return round(sum(i.rating for i in items) / len(items), 2)


feedback_service = FeedbackService()
