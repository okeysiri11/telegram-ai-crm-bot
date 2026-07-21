# CRMService — agro marketplace leads and contacts.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.agro_marketplace.shared.store import AgroStore, agro_store


@dataclass
class AgroLead:
    lead_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    role: str = "buyer"
    source: str = "marketplace"
    status: str = "new"
    notes: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "source": self.source,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class CRMService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create_lead(self, lead: AgroLead) -> AgroLead:
        return self._store.crm_leads.save(lead.lead_id, lead)

    def list_leads(self) -> list[AgroLead]:
        return self._store.crm_leads.list_all()

    def qualify_lead(self, lead_id: str) -> AgroLead | None:
        lead = self._store.crm_leads.get(lead_id)
        if lead is None:
            return None
        lead.status = "qualified"
        return self._store.crm_leads.save(lead_id, lead)


crm_service = CRMService()
