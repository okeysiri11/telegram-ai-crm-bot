"""Confidence Score — Sprint 24.3."""

from __future__ import annotations

from typing import Any


class ConfidenceScore:
    def attach(
        self,
        *,
        prediction: dict[str, Any],
        confidence: float = 0.75,
        factors: list[str] | None = None,
        data_used: list[str] | None = None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        confidence = max(0.0, min(1.0, float(confidence)))
        return {
            **prediction,
            "confidence": confidence,
            "confidence_level": "high" if confidence >= 0.8 else ("medium" if confidence >= 0.5 else "low"),
            "explanation_factors": list(factors or ["historical_trend", "seasonality"]),
            "data_used": list(data_used or []),
            "model_limitations": list(limitations or ["sample_size", "external_shocks"]),
            "explained": True,
        }
