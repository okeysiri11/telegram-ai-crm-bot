# Mobility facade helpers — pool booking alias.

from __future__ import annotations

from applications.auto_marketplace.corporate.engine import CorporateMobilityEngine, corporate_mobility_engine


class MobilityEngine:
    def __init__(self, corporate: CorporateMobilityEngine | None = None) -> None:
        self._corporate = corporate or corporate_mobility_engine

    def book(self, *args, **kwargs):
        return self._corporate.book_pool(*args, **kwargs)

    def metrics(self) -> dict:
        return self._corporate.metrics()


mobility_engine = MobilityEngine()
