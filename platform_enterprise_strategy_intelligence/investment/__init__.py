"""Investment Analyzer — Sprint 24.7."""

from __future__ import annotations

from typing import Any


class InvestmentAnalyzer:
    def analyze(
        self,
        *,
        investment: float,
        annual_return: float,
        cashflow_delta: float = 0.0,
        profit_delta: float = 0.0,
        staff_impact: float = 0.0,
        customer_impact: float = 0.0,
    ) -> dict[str, Any]:
        investment = float(investment)
        annual_return = float(annual_return)
        payback_years = round(investment / annual_return, 2) if annual_return > 0 else None
        roi = round(annual_return / investment, 3) if investment > 0 else 0.0
        return {
            "investment": investment,
            "payback_years": payback_years,
            "roi": roi,
            "cashflow_impact": float(cashflow_delta),
            "profit_impact": float(profit_delta),
            "staff_impact": float(staff_impact),
            "customer_impact": float(customer_impact),
        }
