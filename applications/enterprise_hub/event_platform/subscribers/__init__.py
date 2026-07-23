"""Event subscribers."""

from applications.enterprise_hub.event_platform.subscribers.ai_agents import AiAgentsSubscriber
from applications.enterprise_hub.event_platform.subscribers.analytics import AnalyticsSubscriber
from applications.enterprise_hub.event_platform.subscribers.audit import AuditSubscriber
from applications.enterprise_hub.event_platform.subscribers.integrations import IntegrationsSubscriber
from applications.enterprise_hub.event_platform.subscribers.notifications import NotificationsSubscriber

__all__ = [
    "NotificationsSubscriber",
    "AnalyticsSubscriber",
    "AuditSubscriber",
    "IntegrationsSubscriber",
    "AiAgentsSubscriber",
]
