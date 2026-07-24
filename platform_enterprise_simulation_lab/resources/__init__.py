"""Resource Simulator — Sprint 24.4."""

from __future__ import annotations

from typing import Any


class ResourceSimulator:
    def calculate(self, *, staff_delta: float = 0.0, sales_delta: float = 0.0, baseline_staff: int = 10) -> dict[str, Any]:
        staff_need = max(0, int(round(baseline_staff * (1 + float(staff_delta)))))
        materials = round(100 * (1 + float(sales_delta)), 2)
        equipment = round(50 * (1 + max(0.0, float(staff_delta))), 2)
        financial = round(materials + equipment + staff_need * 20, 2)
        productivity = round(1.0 + float(sales_delta) - abs(float(staff_delta)) * 0.1, 3)
        return {
            "staff_needed": staff_need,
            "materials": materials,
            "equipment": equipment,
            "financial_resources": financial,
            "productivity": productivity,
        }
