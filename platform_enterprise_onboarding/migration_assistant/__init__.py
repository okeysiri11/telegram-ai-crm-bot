"""AI Migration Assistant — Sprint 22.9."""

from __future__ import annotations

from typing import Any


class AIMigrationAssistant:
    def advise(
        self,
        *,
        columns: list[str] | None = None,
        target_fields: list[str] | None = None,
        validation_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        columns = list(columns or [])
        target_fields = list(target_fields or [])
        report = validation_report or {}
        mapping = {}
        for col in columns:
            low = col.lower().replace(" ", "_")
            match = next((t for t in target_fields if t in low or low in t), None)
            if match:
                mapping[col] = match
            elif low in ("client", "customer", "фио"):
                mapping[col] = "name"
            else:
                mapping[col] = None
        quality = 1.0
        if report.get("issue_count"):
            quality = max(0.0, 1.0 - (float(report["issue_count"]) / max(int(report.get("row_count") or 1), 1)))
        risks = []
        if any(v is None for v in mapping.values()):
            risks.append("unmapped_columns")
        if report.get("issue_count", 0) > 0:
            risks.append("validation_errors")
        if quality < 0.8:
            risks.append("low_data_quality")
        return {
            "column_mapping": mapping,
            "detected_errors": list(report.get("issues") or []),
            "suggested_fixes": list(report.get("suggested_fixes") or []),
            "data_quality_score": round(quality, 3),
            "risks": risks,
            "ai_may_act": False,
            "proposes_only": True,
            "mutates_data": False,
        }
