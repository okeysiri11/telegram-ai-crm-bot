"""Event publishers."""

from applications.enterprise_hub.event_platform.publishers.ai import AiPublisher
from applications.enterprise_hub.event_platform.publishers.crm import CrmPublisher
from applications.enterprise_hub.event_platform.publishers.custom import CustomPublisher
from applications.enterprise_hub.event_platform.publishers.erp import ErpPublisher
from applications.enterprise_hub.event_platform.publishers.finance import FinancePublisher
from applications.enterprise_hub.event_platform.publishers.workflow import WorkflowPublisher

__all__ = [
    "CrmPublisher",
    "ErpPublisher",
    "AiPublisher",
    "WorkflowPublisher",
    "FinancePublisher",
    "CustomPublisher",
]
