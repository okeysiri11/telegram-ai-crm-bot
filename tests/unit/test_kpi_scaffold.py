"""Unit tests for analytics KPI scaffold."""

def test_conversion_rate():
    from src.platform.analytics import KpiCalculator

    assert KpiCalculator.conversion_rate(2, 10) == 20.0
    assert KpiCalculator.conversion_rate(0, 0) == 0.0
