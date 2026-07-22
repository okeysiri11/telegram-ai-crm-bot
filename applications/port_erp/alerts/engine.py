# Alerts Engine — congestion, ETA, equipment, customs, weather, capacity.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.digital_twin.events import AlertRaisedEvent
from applications.port_erp.digital_twin.models import AlertSeverity, AlertType, PortAlert
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class AlertsEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    async def raise_alert(
        self,
        *,
        alert_type: AlertType | str,
        title: str,
        message: str = "",
        severity: AlertSeverity | str = AlertSeverity.WARNING,
        related_id: str = "",
    ) -> PortAlert:
        if not title:
            raise ValidationError("title is required")
        atype = AlertType(alert_type) if isinstance(alert_type, str) else alert_type
        sev = AlertSeverity(severity) if isinstance(severity, str) else severity
        alert = PortAlert(
            alert_type=atype,
            severity=sev,
            title=title,
            message=message or title,
            related_id=related_id,
        )
        saved = self._store.port_alerts.save(alert.alert_id, alert)
        await publish(
            AlertRaisedEvent(
                alert_id=saved.alert_id,
                alert_type=saved.alert_type.value,
                severity=saved.severity.value,
            )
        )
        return saved

    def list_alerts(
        self,
        *,
        severity: AlertSeverity | None = None,
        acknowledged: bool | None = None,
    ) -> list[PortAlert]:
        items = self._store.port_alerts.list_all()
        if severity:
            items = [a for a in items if a.severity == severity]
        if acknowledged is not None:
            items = [a for a in items if a.acknowledged is acknowledged]
        return sorted(items, key=lambda a: a.created_at, reverse=True)

    def acknowledge(self, alert_id: str) -> PortAlert:
        alert = self._store.port_alerts.get(alert_id)
        if alert is None:
            raise NotFoundError("PortAlert", alert_id)
        alert.acknowledged = True
        return self._store.port_alerts.save(alert_id, alert)

    def alert_types(self) -> list[str]:
        return [t.value for t in AlertType]


alerts_engine = AlertsEngine()
