"""Event Platform Suite facade — Sprint 20.5."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.event_platform.analytics.event_statistics import EventStatisticsAnalytics
from applications.enterprise_hub.event_platform.analytics.latency import LatencyAnalytics
from applications.enterprise_hub.event_platform.analytics.throughput import ThroughputAnalytics
from applications.enterprise_hub.event_platform.dead_letter_queue import DeadLetterQueue
from applications.enterprise_hub.event_platform.event_bus import EventBus
from applications.enterprise_hub.event_platform.event_dispatcher import EventDispatcher
from applications.enterprise_hub.event_platform.event_manager import EventManager
from applications.enterprise_hub.event_platform.event_registry import EventRegistry
from applications.enterprise_hub.event_platform.event_router import EventRouter
from applications.enterprise_hub.event_platform.event_store import EventStore
from applications.enterprise_hub.event_platform.publishers.ai import AiPublisher
from applications.enterprise_hub.event_platform.publishers.crm import CrmPublisher
from applications.enterprise_hub.event_platform.publishers.custom import CustomPublisher
from applications.enterprise_hub.event_platform.publishers.erp import ErpPublisher
from applications.enterprise_hub.event_platform.publishers.finance import FinancePublisher
from applications.enterprise_hub.event_platform.publishers.workflow import WorkflowPublisher
from applications.enterprise_hub.event_platform.replay_engine import ReplayEngine
from applications.enterprise_hub.event_platform.retry_manager import RetryManager
from applications.enterprise_hub.event_platform.schema_registry import SchemaRegistry
from applications.enterprise_hub.event_platform.subscribers.ai_agents import AiAgentsSubscriber
from applications.enterprise_hub.event_platform.subscribers.analytics import AnalyticsSubscriber
from applications.enterprise_hub.event_platform.subscribers.audit import AuditSubscriber
from applications.enterprise_hub.event_platform.subscribers.integrations import IntegrationsSubscriber
from applications.enterprise_hub.event_platform.subscribers.notifications import NotificationsSubscriber
from applications.enterprise_hub.event_platform.subscription_manager import SubscriptionManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class EventPlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = EventManager(self.store)
        self.bus = EventBus(self.store)
        self.registry = EventRegistry(self.store)
        self.dispatcher = EventDispatcher(self.store)
        self.router = EventRouter(self.store)
        self.event_store = EventStore(self.store)
        self.subscriptions = SubscriptionManager(self.store)
        self.retries = RetryManager(self.store)
        self.dlq = DeadLetterQueue(self.store)
        self.replay = ReplayEngine(self.store)
        self.schemas = SchemaRegistry(self.store)
        self.crm = CrmPublisher(self.store)
        self.erp = ErpPublisher(self.store)
        self.ai = AiPublisher(self.store)
        self.workflow = WorkflowPublisher(self.store)
        self.finance = FinancePublisher(self.store)
        self.custom = CustomPublisher(self.store)
        self.notifications = NotificationsSubscriber(self.store)
        self.analytics_sub = AnalyticsSubscriber(self.store)
        self.audit = AuditSubscriber(self.store)
        self.integrations = IntegrationsSubscriber(self.store)
        self.ai_agents = AiAgentsSubscriber(self.store)
        self.throughput = ThroughputAnalytics(self.store)
        self.latency = LatencyAnalytics(self.store)
        self.statistics = EventStatisticsAnalytics(self.store)

    def dashboard(self) -> dict[str, Any]:
        t = self.throughput.report()
        l = self.latency.report()
        s = self.statistics.report()
        return {
            "throughput_id": t["analytics_id"],
            "latency_id": l["analytics_id"],
            "statistics_id": s["analytics_id"],
            "event_count": s.get("event_count"),
            "dlq_count": s.get("dlq_count"),
            "retry_count": s.get("retry_count"),
            "by_type": s.get("by_type"),
            "queue_load": s.get("queue_load"),
            "avg_backoff_ms": l.get("avg_backoff_ms"),
        }

    def bootstrap(self) -> dict[str, Any]:
        catalog = self.manager.bootstrap_catalog()

        sub_n = self.notifications.subscribe(
            event_types=["LeadCreated", "ContractSigned", "PaymentReceived", "SecurityAlert"]
        )
        sub_a = self.analytics_sub.subscribe(event_types=["LeadCreated", "PaymentReceived", "AIJobFinished", "TaskCompleted"])
        sub_au = self.audit.subscribe(event_types=["UserCreated", "SecurityAlert", "InvoiceApproved", "DocumentUpdated"])
        sub_i = self.integrations.subscribe(event_types=["ShipmentCreated", "PaymentReceived", "ContractSigned"])
        sub_ai = self.ai_agents.subscribe(event_types=["LeadCreated", "AIJobFinished", "DocumentUpdated", "TaskCompleted"])

        d1 = self.crm.publish(payload={"id": "L1", "timestamp": "t0", "entity_id": "lead-1"}, idempotency_key="lead-1")
        d2 = self.finance.publish(
            event_type="PaymentReceived",
            payload={"id": "P1", "timestamp": "t1", "entity_id": "pay-1"},
            idempotency_key="pay-1",
        )
        d3 = self.workflow.publish(payload={"id": "T1", "timestamp": "t2", "entity_id": "task-1"})
        d4 = self.ai.publish(payload={"id": "AI1", "timestamp": "t3", "entity_id": "job-1"})
        d5 = self.erp.publish(payload={"id": "S1", "timestamp": "t4", "entity_id": "ship-1"})
        d6 = self.custom.publish(
            event_type="SecurityAlert",
            payload={"id": "SEC1", "timestamp": "t5", "entity_id": "alert-1"},
            severity="critical",
        )

        # force a DLQ path
        d_fail = self.bus.publish(
            event_type="InvoiceApproved",
            source="finance",
            payload={"id": "INV1", "timestamp": "t6", "entity_id": "inv-1"},
            fail_subscribers=["audit"],
            max_retries=1,
        )

        # idempotent re-publish returns same event
        again = self.crm.publish(
            payload={"id": "L1", "timestamp": "t0", "entity_id": "lead-1"},
            idempotency_key="lead-1",
        )

        replayed = self.replay.replay(event_ids=[d1["event_id"], d2["event_id"]])
        dash = self.dashboard()

        return {
            "bootstrap": True,
            "catalog_count": len(catalog),
            "subscription_ids": [
                sub_n["subscription_id"],
                sub_a["subscription_id"],
                sub_au["subscription_id"],
                sub_i["subscription_id"],
                sub_ai["subscription_id"],
            ],
            "dispatch_crm_id": d1["dispatch_id"],
            "dispatch_finance_id": d2["dispatch_id"],
            "dispatch_workflow_id": d3["dispatch_id"],
            "dispatch_ai_id": d4["dispatch_id"],
            "dispatch_erp_id": d5["dispatch_id"],
            "dispatch_security_id": d6["dispatch_id"],
            "dispatch_fail_id": d_fail["dispatch_id"],
            "idempotent_same_event": again["event_id"] == d1["event_id"],
            "replay_id": replayed["replay_id"],
            "dashboard": dash,
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "manager": self.manager.status(),
            "retries": self.retries.status(),
            "dlq": self.dlq.status(),
            "subscriptions": self.subscriptions.status(),
        }


event_platform = EventPlatformSuite()
