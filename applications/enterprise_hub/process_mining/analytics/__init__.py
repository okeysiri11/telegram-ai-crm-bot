"""Process mining analytics."""

from applications.enterprise_hub.process_mining.analytics.efficiency import EfficiencyAnalytics
from applications.enterprise_hub.process_mining.analytics.kpi import ProcessKpi
from applications.enterprise_hub.process_mining.analytics.recommendations import RecommendationAnalytics
from applications.enterprise_hub.process_mining.analytics.sla import SlaAnalytics

__all__ = ["EfficiencyAnalytics", "ProcessKpi", "RecommendationAnalytics", "SlaAnalytics"]
