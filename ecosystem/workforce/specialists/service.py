# Specialist agents — domain experts under departments.

from __future__ import annotations

from ecosystem.shared.exceptions import NotFoundError, ValidationError
from ecosystem.shared.store import EcosystemStore, ecosystem_store
from ecosystem.workforce.models import SPECIALIST_DEPARTMENT, SpecialistAgent, SpecialistType


SPECIALIST_SKILLS: dict[SpecialistType, list[str]] = {
    SpecialistType.SALES: ["lead_qualification", "negotiation", "crm"],
    SpecialistType.FINANCIAL: ["invoicing", "settlement", "forecasting"],
    SpecialistType.MARKETING: ["campaigns", "content", "attribution"],
    SpecialistType.DEVELOPER: ["integrations", "apis", "automation"],
    SpecialistType.SUPPORT: ["tickets", "escalation", "customer_care"],
    SpecialistType.LAW: ["contracts", "compliance", "review"],
    SpecialistType.ANALYTICS: ["kpis", "reporting", "insights"],
    SpecialistType.INVENTORY: ["stock", "reservation", "logistics"],
}


class SpecialistService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._seed()

    def _seed(self) -> None:
        if self._store.specialists.count() > 0:
            return
        for stype in SpecialistType:
            agent = SpecialistAgent(
                specialist_type=stype,
                name=stype.value.replace("_", " ").title(),
                department_type=SPECIALIST_DEPARTMENT[stype],
                skills=list(SPECIALIST_SKILLS[stype]),
            )
            self._store.specialists.save(agent.specialist_id, agent)

    def _ensure_seeded(self) -> None:
        if self._store.specialists.count() == 0:
            self._seed()

    def list_specialists(self, *, department_type=None) -> list[SpecialistAgent]:
        self._ensure_seeded()
        specialists = self._store.specialists.list_all()
        if department_type:
            specialists = [s for s in specialists if s.department_type == department_type]
        return specialists

    def get(self, specialist_id: str) -> SpecialistAgent:
        self._ensure_seeded()
        specialist = self._store.specialists.get(specialist_id)
        if specialist is None:
            raise NotFoundError("Specialist", specialist_id)
        return specialist

    def get_by_type(self, specialist_type: SpecialistType) -> SpecialistAgent:
        self._ensure_seeded()
        for specialist in self._store.specialists.list_all():
            if specialist.specialist_type == specialist_type:
                return specialist
        raise NotFoundError("Specialist", specialist_type.value)

    def assignable(self, specialist_type: SpecialistType | None = None) -> SpecialistAgent:
        specialists = self.list_specialists()
        if specialist_type:
            specialists = [s for s in specialists if s.specialist_type == specialist_type]
        available = [s for s in specialists if s.is_active and s.active_tasks < s.max_tasks]
        if not available:
            raise ValidationError("No available specialists")
        return min(available, key=lambda s: s.active_tasks)

    def increment_load(self, specialist_id: str, delta: int = 1) -> SpecialistAgent:
        specialist = self.get(specialist_id)
        specialist.active_tasks = max(0, specialist.active_tasks + delta)
        self._store.specialists.save(specialist_id, specialist)
        return specialist


specialist_service = SpecialistService()
