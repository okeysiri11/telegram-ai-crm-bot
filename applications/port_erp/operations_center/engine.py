# Operations Center Engine — control-room view over twin, alerts, predictions.

from __future__ import annotations

from applications.port_erp.alerts.engine import AlertsEngine, alerts_engine
from applications.port_erp.digital_twin.engine import DigitalTwinEngine, digital_twin_engine
from applications.port_erp.digital_twin.models import AlertSeverity, AlertType
from applications.port_erp.prediction.engine import PredictiveAnalyticsEngine, predictive_analytics_engine


class OperationsCenterEngine:
    def __init__(
        self,
        twin: DigitalTwinEngine | None = None,
        alerts: AlertsEngine | None = None,
        prediction: PredictiveAnalyticsEngine | None = None,
    ) -> None:
        self.twin = twin or digital_twin_engine
        self.alerts = alerts or alerts_engine
        self.prediction = prediction or predictive_analytics_engine

    async def refresh(self, *, port_id: str = "") -> dict:
        snap = await self.twin.snapshot(port_id=port_id)
        if snap.utilization >= 0.9:
            await self.alerts.raise_alert(
                alert_type=AlertType.CAPACITY_THRESHOLD,
                title="Port capacity threshold exceeded",
                message=f"Utilization {snap.utilization}",
                severity=AlertSeverity.CRITICAL,
            )
        if snap.weather.condition.value == "storm":
            await self.alerts.raise_alert(
                alert_type=AlertType.WEATHER_WARNING,
                title="Storm weather warning",
                message="Digital twin weather is storm",
                severity=AlertSeverity.WARNING,
            )
        queue = self.prediction.predict_queue()
        congestion = self.prediction.predict_congestion()
        return {
            "snapshot": snap.to_dict(),
            "queue_prediction": queue.to_dict(),
            "congestion_prediction": congestion.to_dict(),
            "open_alerts": [a.to_dict() for a in self.alerts.list_alerts(acknowledged=False)],
        }

    def overview(self) -> dict:
        return {
            "twin": self.twin.state(),
            "alerts": [a.to_dict() for a in self.alerts.list_alerts()[:20]],
            "predictions": [p.to_dict() for p in self.prediction.list_predictions()[:20]],
        }


operations_center_engine = OperationsCenterEngine()
