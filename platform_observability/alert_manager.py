# Alert manager — routing, deduplication, rate limiting.

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from platform_observability.models import AlertRecord, AlertSeverity, AlertState
from platform_observability.observability_events import AlertRaisedEvent, AlertResolvedEvent

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(
        self,
        *,
        dedup_window_seconds: float = 300,
        rate_limit_per_minute: int = 30,
    ) -> None:
        self._alerts: dict[str, AlertRecord] = {}
        self._by_fingerprint: dict[str, str] = {}
        self._dedup_window = dedup_window_seconds
        self._rate_limit = rate_limit_per_minute
        self._raise_timestamps: list[float] = []
        self._routes: dict[str, list[str]] = {
            "warning": ["operations"],
            "critical": ["operations", "owner"],
        }

    def reset(self) -> None:
        self._alerts.clear()
        self._by_fingerprint.clear()
        self._raise_timestamps.clear()

    def _fingerprint(self, name: str, source: str) -> str:
        return hashlib.sha256(f"{name}:{source}".encode()).hexdigest()[:16]

    def _rate_allowed(self) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        self._raise_timestamps = [ts for ts in self._raise_timestamps if ts > cutoff]
        if len(self._raise_timestamps) >= self._rate_limit:
            return False
        self._raise_timestamps.append(now)
        return True

    async def raise_alert(
        self,
        *,
        name: str,
        severity: str,
        source: str,
        message: str,
    ) -> AlertRecord | None:
        fp = self._fingerprint(name, source)
        existing_id = self._by_fingerprint.get(fp)
        if existing_id:
            existing = self._alerts.get(existing_id)
            if existing and existing.state == AlertState.OPEN.value:
                age = (datetime.now(timezone.utc) - existing.raised_at).total_seconds()
                if age < self._dedup_window:
                    existing.count += 1
                    return existing

        if not self._rate_allowed():
            logger.warning("alert_rate_limited name=%s", name)
            return None

        alert = AlertRecord(
            alert_id=str(uuid.uuid4()),
            name=name,
            severity=severity,
            state=AlertState.OPEN.value,
            source=source,
            message=message,
            fingerprint=fp,
        )
        self._alerts[alert.alert_id] = alert
        self._by_fingerprint[fp] = alert.alert_id

        await self._publish_raised(alert)
        logging_service_ref = __import__(
            "platform_observability.logging_service", fromlist=["logging_service"]
        ).logging_service
        logging_service_ref.warning(
            f"Alert raised: {name}",
            component="alert_manager",
            extra={"severity": severity, "source": source},
        )
        return alert

    async def resolve(self, alert_id: str) -> AlertRecord:
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise KeyError(f"Alert {alert_id} not found")
        alert.state = AlertState.RECOVERED.value
        alert.resolved_at = datetime.now(timezone.utc)
        await self._publish_resolved(alert)
        return alert

    async def _publish_raised(self, alert: AlertRecord) -> None:
        from events.event_bus import publish

        await publish(
            AlertRaisedEvent(
                alert_id=alert.alert_id,
                name=alert.name,
                severity=alert.severity,
                source=alert.source,
                message=alert.message,
            )
        )

    async def _publish_resolved(self, alert: AlertRecord) -> None:
        from events.event_bus import publish

        await publish(
            AlertResolvedEvent(
                alert_id=alert.alert_id,
                name=alert.name,
                source=alert.source,
            )
        )

    def list_alerts(self, *, state: str | None = None) -> list[AlertRecord]:
        alerts = list(self._alerts.values())
        if state:
            alerts = [a for a in alerts if a.state == state]
        return alerts

    def routes_for(self, severity: str) -> list[str]:
        return list(self._routes.get(severity, ["operations"]))


alert_manager = AlertManager()
