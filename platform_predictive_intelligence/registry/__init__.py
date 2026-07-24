"""Prediction Registry — Sprint 24.3."""

from __future__ import annotations

from typing import Any


class PredictionRegistry:
    def __init__(self) -> None:
        self._models: dict[str, dict[str, Any]] = {}

    def register(
        self,
        *,
        model_id: str,
        domain: str,
        prediction_type: str,
        data_sources: list[str] | None = None,
        accuracy: float = 0.8,
        status: str = "active",
    ) -> dict[str, Any]:
        if not model_id:
            raise ValueError("model_id is required")
        model = {
            "model_id": model_id,
            "domain": domain,
            "prediction_type": prediction_type,
            "data_sources": list(data_sources or []),
            "accuracy": float(accuracy),
            "training_history": [],
            "status": status or "active",
        }
        self._models[model_id] = model
        return dict(model)

    def list_models(self, *, status: str | None = None) -> list[dict[str, Any]]:
        items = [dict(m) for m in self._models.values()]
        if status:
            items = [m for m in items if m.get("status") == status]
        return items

    def record_training(self, model_id: str, *, note: str, accuracy: float | None = None) -> dict[str, Any]:
        m = self._models.get(model_id)
        if not m:
            raise ValueError(f"unknown model: {model_id}")
        hist = list(m.get("training_history") or [])
        hist.append({"note": note, "accuracy": accuracy if accuracy is not None else m.get("accuracy")})
        m["training_history"] = hist[-50:]
        if accuracy is not None:
            m["accuracy"] = float(accuracy)
        return dict(m)

    def get(self, model_id: str) -> dict[str, Any] | None:
        m = self._models.get(model_id)
        return dict(m) if m else None
