# Broker Operations Engine — broker cases linked to shipments/declarations.

from __future__ import annotations

import time

from applications.port_erp.customs.models import BrokerCase, BrokerCaseStatus
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class BrokerOperationsEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def open_case(self, case: BrokerCase) -> BrokerCase:
        if not case.broker_id:
            raise ValidationError("broker_id is required")
        if not case.shipment_id and not case.declaration_id:
            raise ValidationError("shipment_id or declaration_id is required")
        return self._store.broker_cases.save(case.case_id, case)

    def get(self, case_id: str) -> BrokerCase:
        case = self._store.broker_cases.get(case_id)
        if case is None:
            raise NotFoundError("BrokerCase", case_id)
        return case

    def list_cases(self, *, broker_id: str | None = None) -> list[BrokerCase]:
        items = self._store.broker_cases.list_all()
        if broker_id:
            items = [c for c in items if c.broker_id == broker_id]
        return items

    def advance(self, case_id: str, status: BrokerCaseStatus | str) -> BrokerCase:
        case = self.get(case_id)
        case.status = BrokerCaseStatus(status) if isinstance(status, str) else status
        if case.status == BrokerCaseStatus.CLOSED:
            case.closed_at = time.time()
        return self._store.broker_cases.save(case_id, case)

    def clear(self, case_id: str, *, notes: str = "") -> BrokerCase:
        case = self.get(case_id)
        case.status = BrokerCaseStatus.CLEARED
        if notes:
            case.notes = notes
        return self._store.broker_cases.save(case_id, case)


broker_operations_engine = BrokerOperationsEngine()
