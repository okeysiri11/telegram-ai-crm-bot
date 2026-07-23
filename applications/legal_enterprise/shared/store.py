"""Shared store — Legal Enterprise (Sprint 17.0)."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EntityStore(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def save(self, key: str, item: T) -> T:
        self._items[key] = item
        return item

    def get(self, key: str) -> T | None:
        return self._items.get(key)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def reset(self) -> None:
        self._items.clear()


class LegalEnterpriseStore:
    def __init__(self) -> None:
        # Legal Registry
        self.legal_entities: EntityStore = EntityStore()
        self.individuals: EntityStore = EntityStore()
        self.attorneys: EntityStore = EntityStore()
        self.judges: EntityStore = EntityStore()
        self.agencies: EntityStore = EntityStore()
        self.legal_roles: EntityStore = EntityStore()
        # Legislation Registry
        self.constitutions: EntityStore = EntityStore()
        self.civil_codes: EntityStore = EntityStore()
        self.commercial_codes: EntityStore = EntityStore()
        self.criminal_codes: EntityStore = EntityStore()
        self.administrative_codes: EntityStore = EntityStore()
        self.tax_codes: EntityStore = EntityStore()
        self.labor_codes: EntityStore = EntityStore()
        self.treaties: EntityStore = EntityStore()
        self.legislation_versions: EntityStore = EntityStore()
        # Court Infrastructure
        self.courts: EntityStore = EntityStore()
        self.court_hierarchies: EntityStore = EntityStore()
        self.jurisdictions: EntityStore = EntityStore()
        self.case_categories: EntityStore = EntityStore()
        # Case Management
        self.cases: EntityStore = EntityStore()
        self.case_statuses: EntityStore = EntityStore()
        self.case_timelines: EntityStore = EntityStore()
        self.participants: EntityStore = EntityStore()
        self.documents: EntityStore = EntityStore()
        self.evidence: EntityStore = EntityStore()
        self.tasks: EntityStore = EntityStore()
        self.case_notes: EntityStore = EntityStore()
        # Knowledge + Dashboard
        self.knowledge: EntityStore = EntityStore()
        self.relationships: EntityStore = EntityStore()
        self.dashboards: EntityStore = EntityStore()
        # Sprint 17.1 — Legislation Intelligence
        self.li_constitutions: EntityStore = EntityStore()
        self.li_codes: EntityStore = EntityStore()
        self.li_laws: EntityStore = EntityStore()
        self.li_regulations: EntityStore = EntityStore()
        self.li_resolutions: EntityStore = EntityStore()
        self.li_orders: EntityStore = EntityStore()
        self.li_treaties: EntityStore = EntityStore()
        self.li_local_regs: EntityStore = EntityStore()
        self.li_articles: EntityStore = EntityStore()
        self.li_history: EntityStore = EntityStore()
        self.li_comparisons: EntityStore = EntityStore()
        self.li_amendments: EntityStore = EntityStore()
        self.li_repealed: EntityStore = EntityStore()
        self.li_effective_dates: EntityStore = EntityStore()
        self.li_snapshots: EntityStore = EntityStore()
        self.li_classifications: EntityStore = EntityStore()
        self.li_searches: EntityStore = EntityStore()
        self.li_cross_refs: EntityStore = EntityStore()
        self.li_conflicts: EntityStore = EntityStore()
        self.li_duplicates: EntityStore = EntityStore()
        self.li_analyses: EntityStore = EntityStore()
        self.li_knowledge: EntityStore = EntityStore()
        self.li_dashboards: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


legal_enterprise_store = LegalEnterpriseStore()
