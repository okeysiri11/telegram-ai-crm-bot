# Predictive Analytics Engine — queue, congestion, dwell, ETA accuracy.

from __future__ import annotations

from applications.port_erp.digital_twin.models import PredictionResult
from applications.port_erp.shared.store import PortStore, port_store


class PredictiveAnalyticsEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def predict_queue(self, *, gate_id: str = "", horizon_hours: float = 6.0) -> PredictionResult:
        visits = self._store.gate_visits.count()
        value = float(max(visits, 1) * (1.2 if horizon_hours >= 6 else 1.0))
        pred = PredictionResult(
            prediction_type="queue",
            subject=gate_id or "all_gates",
            value=round(value, 1),
            unit="trucks",
            confidence=0.72,
            horizon_hours=horizon_hours,
        )
        return self._store.predictions.save(pred.prediction_id, pred)

    def predict_congestion(self, *, terminal_id: str = "") -> PredictionResult:
        berths = self._store.berths.count() or 1
        occupied = len([b for b in self._store.berths.list_all() if getattr(b, "status", "") == "occupied"])
        ratio = occupied / berths
        pred = PredictionResult(
            prediction_type="congestion",
            subject=terminal_id or "port",
            value=round(min(1.0, ratio * 1.15), 3),
            unit="index",
            confidence=0.68,
            metadata={"berths_occupied": occupied, "berths_total": berths},
        )
        return self._store.predictions.save(pred.prediction_id, pred)

    def predict_dwell_time(self) -> PredictionResult:
        containers = self._store.containers.count()
        pred = PredictionResult(
            prediction_type="dwell_time",
            subject="containers",
            value=round(36.0 + containers * 0.5, 1),
            unit="hours",
            confidence=0.65,
        )
        return self._store.predictions.save(pred.prediction_id, pred)

    def eta_accuracy(self) -> PredictionResult:
        preds = self._store.eta_predictions.count()
        accuracy = 0.82 if preds else 0.75
        pred = PredictionResult(
            prediction_type="eta_accuracy",
            subject="fleet",
            value=accuracy,
            unit="ratio",
            confidence=0.7,
            metadata={"samples": preds},
        )
        return self._store.predictions.save(pred.prediction_id, pred)

    def list_predictions(self) -> list[PredictionResult]:
        return sorted(self._store.predictions.list_all(), key=lambda p: p.created_at, reverse=True)


predictive_analytics_engine = PredictiveAnalyticsEngine()
