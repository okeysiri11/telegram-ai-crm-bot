# Company Registry — shipping lines, forwarders, brokers, carriers, operators.

from __future__ import annotations

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import (
    Carrier,
    CustomsBroker,
    Forwarder,
    PortOperator,
    ShippingLine,
)
from applications.port_erp.shared.store import PortStore, port_store


class CompanyRegistry:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register_shipping_line(self, line: ShippingLine) -> ShippingLine:
        if not line.name:
            raise ValidationError("name is required")
        return self._store.shipping_lines.save(line.shipping_line_id, line)

    def register_forwarder(self, forwarder: Forwarder) -> Forwarder:
        if not forwarder.name:
            raise ValidationError("name is required")
        return self._store.forwarders.save(forwarder.forwarder_id, forwarder)

    def register_broker(self, broker: CustomsBroker) -> CustomsBroker:
        if not broker.name:
            raise ValidationError("name is required")
        return self._store.customs_brokers.save(broker.broker_id, broker)

    def register_carrier(self, carrier: Carrier) -> Carrier:
        if not carrier.name:
            raise ValidationError("name is required")
        return self._store.carriers.save(carrier.carrier_id, carrier)

    def register_operator(self, operator: PortOperator) -> PortOperator:
        if not operator.name:
            raise ValidationError("name is required")
        return self._store.port_operators.save(operator.operator_id, operator)

    def list_companies(self) -> dict[str, list]:
        return {
            "shipping_lines": [c.to_dict() for c in self._store.shipping_lines.list_all()],
            "forwarders": [c.to_dict() for c in self._store.forwarders.list_all()],
            "customs_brokers": [c.to_dict() for c in self._store.customs_brokers.list_all()],
            "carriers": [c.to_dict() for c in self._store.carriers.list_all()],
            "port_operators": [c.to_dict() for c in self._store.port_operators.list_all()],
        }

    def get_shipping_line(self, shipping_line_id: str) -> ShippingLine:
        line = self._store.shipping_lines.get(shipping_line_id)
        if line is None:
            raise NotFoundError("ShippingLine", shipping_line_id)
        return line


company_registry = CompanyRegistry()
