"""Knowledge analytics."""

from applications.enterprise_hub.knowledge_platform.analytics.quality import QualityAnalytics
from applications.enterprise_hub.knowledge_platform.analytics.relevance import RelevanceAnalytics
from applications.enterprise_hub.knowledge_platform.analytics.usage import UsageAnalytics

__all__ = ["UsageAnalytics", "QualityAnalytics", "RelevanceAnalytics"]
