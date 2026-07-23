"""Observability Suite facade — Sprint 19.9."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.observability.alerting import AlertingEngine
from applications.enterprise_hub.observability.dashboards import OperationsDashboard
from applications.enterprise_hub.observability.diagnostics import DiagnosticsEngine
from applications.enterprise_hub.observability.health import HealthMonitor
from applications.enterprise_hub.observability.incidents import IncidentManager
from applications.enterprise_hub.observability.logging import CentralizedLogging
from applications.enterprise_hub.observability.metrics import MetricsPlatform
from applications.enterprise_hub.observability.monitoring import MonitoringEngine
from applications.enterprise_hub.observability.service_registry import ServiceRegistry
from applications.enterprise_hub.observability.tracing import DistributedTracing
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class ObservabilitySuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.monitoring = MonitoringEngine(self.store)
        self.metrics = MetricsPlatform(self.store)
        self.tracing = DistributedTracing(self.store)
        self.logging = CentralizedLogging(self.store)
        self.health = HealthMonitor(self.store)
        self.alerting = AlertingEngine(self.store)
        self.incidents = IncidentManager(self.store)
        self.diagnostics = DiagnosticsEngine(self.store)
        self.services = ServiceRegistry(self.store)
        self.dashboard = OperationsDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        api_gw = self.services.register(
            name="api-gateway", kind="microservice", version="5.3.9", owners=["platform"]
        )
        crm = self.services.register(
            name="crm-core", kind="microservice", version="5.3.9", dependencies=["api-gateway"]
        )
        agent = self.services.register(
            name="finance-agent", kind="ai_agent", version="1.0", owners=["ai"]
        )
        integ = self.services.register(
            name="stripe-eip", kind="integration", version="1.0", owners=["finance"]
        )
        queue = self.services.register(name="notifications-queue", kind="queue", version="1.0")
        bg = self.services.register(name="settlement-worker", kind="background", version="1.0")

        for sid in (
            api_gw["service_id"],
            crm["service_id"],
            agent["service_id"],
            integ["service_id"],
            queue["service_id"],
            bg["service_id"],
        ):
            self.services.set_health(service_id=sid, health_status="healthy")

        m_cpu = self.metrics.record(kind="cpu", value=42.5, labels={"host": "hub-1"})
        m_ram = self.metrics.record(kind="ram", value=68.0, labels={"host": "hub-1"})
        m_disk = self.metrics.record(kind="disk", value=55.0)
        m_net = self.metrics.record(kind="network", value=120.0)
        m_db = self.metrics.record(kind="database", value=12.0)
        m_q = self.metrics.record(kind="queue", value=3.0)
        m_api = self.metrics.record(kind="api", value=95.0, labels={"p95_ms": 95})
        m_tok = self.metrics.record(kind="ai_tokens", value=12500)
        m_cost = self.metrics.record(kind="ai_cost", value=18.4)
        m_users = self.metrics.record(kind="active_users", value=87)
        m_sess = self.metrics.record(kind="active_sessions", value=64)

        h1 = self.health.check(target="api-gateway", target_type="service", status="healthy")
        h2 = self.health.check(target="postgres", target_type="database", status="healthy")
        h3 = self.health.check(target="redis-queue", target_type="queue", status="healthy")
        h4 = self.health.check(target="stripe", target_type="integration", status="degraded", detail="latency")
        h5 = self.health.check(target="gpt-model", target_type="ai_model", status="healthy")

        col_sys = self.monitoring.collect(collector="system", payload={"cpu": 42.5})
        col_app = self.monitoring.collect(collector="application", payload={"rps": 120})
        col_ai = self.monitoring.collect(collector="ai_agents", payload={"active": 7})
        col_db = self.monitoring.collect(collector="database", payload={"connections": 40})
        col_net = self.monitoring.collect(collector="network", payload={"mbps": 200})
        col_int = self.monitoring.collect(collector="integrations", payload={"ok": 12, "fail": 1})

        exp_p = self.monitoring.export(exporter="prometheus", payload={"job": "hub"})
        exp_g = self.monitoring.export(exporter="grafana", payload={"dashboard": "ops"})
        exp_e = self.monitoring.export(exporter="elastic", payload={"index": "logs"})
        exp_l = self.monitoring.export(exporter="loki", payload={"stream": "hub"})
        exp_o = self.monitoring.export(exporter="otel", payload={"endpoint": "otel-collector"})

        corr = "corr_bootstrap_19_9"
        log_app = self.logging.write(
            kind="application", message="request accepted", service="api-gateway", user="cfo@bidex.io", correlation_id=corr
        )
        log_ai = self.logging.write(
            kind="ai", message="agent completed task", service="finance-agent", ai_agent="finance_agent", correlation_id=corr
        )
        log_int = self.logging.write(
            kind="integration", message="stripe sync ok", service="stripe-eip", correlation_id=corr
        )
        log_sec = self.logging.write(kind="security", message="login ok", user="admin@bidex.io", correlation_id=corr)
        log_err = self.logging.write(
            kind="error", message="stripe timeout", service="stripe-eip", correlation_id=corr
        )
        log_audit = self.logging.write(kind="audit", message="role changed", user="admin@bidex.io")
        search = self.logging.search(correlation_id=corr)

        trace = self.tracing.start(name="invoice_notify", correlation_id=corr)
        self.tracing.span(trace_id=trace["trace_id"], service="client", operation="submit", duration_ms=5)
        self.tracing.span(trace_id=trace["trace_id"], service="api-gateway", operation="route", duration_ms=12)
        self.tracing.span(trace_id=trace["trace_id"], service="crm-core", operation="load", duration_ms=28)
        self.tracing.span(trace_id=trace["trace_id"], service="finance-agent", operation="reason", duration_ms=140)
        self.tracing.span(trace_id=trace["trace_id"], service="database", operation="write", duration_ms=18)
        self.tracing.span(trace_id=trace["trace_id"], service="notifications", operation="send", duration_ms=22)
        finished = self.tracing.finish(trace_id=trace["trace_id"], status="ok")

        alert_w = self.alerting.fire(title="Stripe latency elevated", level="warning", channel="telegram", service="stripe-eip")
        alert_e = self.alerting.fire(title="DB connection spike", level="error", channel="email", service="postgres")
        alert_c = self.alerting.fire(
            title="API gateway outage risk", level="critical", channel="sms", service="api-gateway", escalate=True
        )
        alert_i = self.alerting.fire(title="Nightly jobs started", level="info", channel="webhook", service="settlement-worker")
        alert_p = self.alerting.fire(title="Queue backlog", level="warning", channel="push", service="notifications-queue")

        inc = self.incidents.open(
            service="stripe-eip",
            severity="error",
            owner="finance-ops",
            root_cause="upstream timeout",
            sla_minutes=30,
        )
        inc2 = self.incidents.update(
            incident_id=inc["incident_id"],
            status="investigating",
            note="checking EIP adapter",
        )
        inc3 = self.incidents.update(
            incident_id=inc["incident_id"],
            status="resolved",
            resolution="increased timeout + retry",
            note="mitigated",
        )

        diag = self.diagnostics.analyze(
            subject="stripe-eip",
            error="timeout",
            logs=["stripe timeout", "retry scheduled"],
        )

        dash_p = self.dashboard.render(dashboard_type="platform")
        dash_i = self.dashboard.render(dashboard_type="infrastructure")
        dash_ai = self.dashboard.render(dashboard_type="ai")
        dash_int = self.dashboard.render(dashboard_type="integrations")
        dash_b = self.dashboard.render(dashboard_type="business")

        return {
            "bootstrap": True,
            "service_api_gateway_id": api_gw["service_id"],
            "service_crm_id": crm["service_id"],
            "service_agent_id": agent["service_id"],
            "service_integration_id": integ["service_id"],
            "service_queue_id": queue["service_id"],
            "service_background_id": bg["service_id"],
            "metric_cpu_id": m_cpu["metric_id"],
            "metric_ram_id": m_ram["metric_id"],
            "metric_disk_id": m_disk["metric_id"],
            "metric_network_id": m_net["metric_id"],
            "metric_database_id": m_db["metric_id"],
            "metric_queue_id": m_q["metric_id"],
            "metric_api_id": m_api["metric_id"],
            "metric_ai_tokens_id": m_tok["metric_id"],
            "metric_ai_cost_id": m_cost["metric_id"],
            "metric_active_users_id": m_users["metric_id"],
            "metric_active_sessions_id": m_sess["metric_id"],
            "health_api_id": h1["health_id"],
            "health_db_id": h2["health_id"],
            "health_queue_id": h3["health_id"],
            "health_integration_id": h4["health_id"],
            "health_ai_id": h5["health_id"],
            "collection_system_id": col_sys["collection_id"],
            "collection_application_id": col_app["collection_id"],
            "collection_ai_id": col_ai["collection_id"],
            "collection_database_id": col_db["collection_id"],
            "collection_network_id": col_net["collection_id"],
            "collection_integrations_id": col_int["collection_id"],
            "export_prometheus_id": exp_p["export_id"],
            "export_grafana_id": exp_g["export_id"],
            "export_elastic_id": exp_e["export_id"],
            "export_loki_id": exp_l["export_id"],
            "export_otel_id": exp_o["export_id"],
            "log_application_id": log_app["log_id"],
            "log_ai_id": log_ai["log_id"],
            "log_integration_id": log_int["log_id"],
            "log_security_id": log_sec["log_id"],
            "log_error_id": log_err["log_id"],
            "log_audit_id": log_audit["log_id"],
            "log_search_id": search["search_id"],
            "trace_id": finished["trace_id"],
            "alert_warning_id": alert_w["alert_id"],
            "alert_error_id": alert_e["alert_id"],
            "alert_critical_id": alert_c["alert_id"],
            "alert_info_id": alert_i["alert_id"],
            "alert_push_id": alert_p["alert_id"],
            "incident_id": inc["incident_id"],
            "incident_investigating_id": inc2["incident_id"],
            "incident_resolved_id": inc3["incident_id"],
            "diagnostic_id": diag["diagnostic_id"],
            "dashboard_platform_id": dash_p["dashboard_id"],
            "dashboard_infrastructure_id": dash_i["dashboard_id"],
            "dashboard_ai_id": dash_ai["dashboard_id"],
            "dashboard_integrations_id": dash_int["dashboard_id"],
            "dashboard_business_id": dash_b["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "monitoring": self.monitoring.status(),
            "metrics": self.metrics.status(),
            "tracing": self.tracing.status(),
            "logging": self.logging.status(),
            "health": self.health.status(),
            "alerting": self.alerting.status(),
            "incidents": self.incidents.status(),
            "diagnostics": self.diagnostics.status(),
            "services": self.services.status(),
            "dashboard": self.dashboard.status(),
        }


observability = ObservabilitySuite()
