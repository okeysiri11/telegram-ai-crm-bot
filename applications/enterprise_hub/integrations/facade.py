"""EIP Suite facade — Sprint 19.6."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.integrations.integration_engine import IntegrationEngine
from applications.enterprise_hub.integrations.integration_manager import IntegrationManager
from applications.enterprise_hub.integrations.integration_monitor import IntegrationMonitor
from applications.enterprise_hub.integrations.integration_registry import IntegrationRegistry
from applications.enterprise_hub.integrations.integration_scheduler import IntegrationScheduler
from applications.enterprise_hub.integrations.integration_security import IntegrationSecurity
from applications.enterprise_hub.integrations.mapping import (
    DataTransformer,
    FieldMapper,
    MappingValidator,
)
from applications.enterprise_hub.integrations.services import AIIntegrationAssistant, EIPDashboard
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class IntegrationPlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = IntegrationRegistry(self.store)
        self.manager = IntegrationManager(self.store, registry=self.registry)
        self.engine = IntegrationEngine(self.store)
        self.monitor = IntegrationMonitor(self.store)
        self.scheduler = IntegrationScheduler(self.store)
        self.security = IntegrationSecurity(self.store)
        self.mapper = FieldMapper(self.store)
        self.transformer = DataTransformer(self.store)
        self.validator = MappingValidator(self.store)
        self.ai = AIIntegrationAssistant(self.store)
        self.dashboard = EIPDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        tg = self.manager.register(
            name="Telegram Bot Bridge",
            protocol="rest",
            adapter="telegram",
            owner="comms",
            connection={"base_url": "https://api.telegram.org"},
            permissions=["send", "receive"],
        )
        stripe = self.manager.register(
            name="Stripe Payments",
            protocol="rest",
            adapter="stripe",
            owner="finance",
            connection={"base_url": "https://api.stripe.com"},
        )
        mono = self.manager.register(
            name="MonoBank",
            protocol="rest",
            adapter="monobank",
            owner="finance",
        )
        privat = self.manager.register(
            name="PrivatBank",
            protocol="soap",
            adapter="privatbank",
            owner="finance",
        )
        drive = self.manager.register(
            name="Google Drive",
            protocol="rest",
            adapter="google_drive",
            owner="docs",
        )
        openai = self.manager.register(
            name="OpenAI",
            protocol="rest",
            adapter="openai",
            owner="ai",
        )
        anthropic = self.manager.register(
            name="Anthropic",
            protocol="rest",
            adapter="anthropic",
            owner="ai",
        )
        kafka = self.manager.register(
            name="Enterprise Kafka Bus",
            protocol="kafka",
            adapter="custom",
            owner="platform",
            connection={"brokers": "kafka:9092"},
        )

        start_tg = self.manager.start(integration_id=tg["integration_id"])
        start_stripe = self.manager.start(integration_id=stripe["integration_id"])
        upd = self.manager.update(integration_id=openai["integration_id"], version="1.1")
        journal = self.manager.journal(
            integration_id=tg["integration_id"], detail="bootstrap registered"
        )

        rest = self.engine.connect(protocol="rest", endpoint="/health", method="GET")
        gql = self.engine.connect(protocol="graphql", endpoint="/graphql", payload={"query": "{ok}"})
        ws = self.engine.connect(protocol="websocket", endpoint="wss://hub/events")
        adp_tg = self.engine.adapt(adapter="telegram", operation="send_message", payload={"text": "hi"})
        adp_bin = self.engine.adapt(adapter="binance", operation="ticker", payload={"symbol": "BTCUSDT"})
        sync = self.engine.sync(integration_id=stripe["integration_id"], mode="incremental", records=25)
        sync2 = self.engine.sync(integration_id=mono["integration_id"], mode="two_way", records=10)
        retry = self.engine.retry(
            integration_id=privat["integration_id"],
            attempt=2,
            error="timeout",
            fallback_route="rest",
        )

        mapped = self.mapper.map_fields(
            source_fields={"cust_name": "Acme", "amt": 100},
            mapping={"cust_name": "customer", "amt": "amount"},
        )
        xf = self.transformer.transform(data={"Name": "Acme", "Status": "OK"}, operation="normalize")
        val = self.validator.validate(data=mapped["result"], required=["customer", "amount"])

        sec = self.security.configure(
            integration_id=stripe["integration_id"], method="oauth2", secret_ref="vault://stripe"
        )
        rot = self.security.rotate_token(security_id=sec["security_id"])
        sec_jwt = self.security.configure(
            integration_id=openai["integration_id"], method="api_key"
        )

        mon = self.monitor.snapshot(
            integration_id=tg["integration_id"],
            latency_ms=42.0,
            errors=0,
            requests=12,
            rate_limit_remaining=988,
            sync_success_rate=1.0,
        )
        mon2 = self.monitor.snapshot(
            integration_id=stripe["integration_id"], latency_ms=90.0, requests=5
        )

        sched = self.scheduler.schedule(
            integration_id=drive["integration_id"],
            expression="0 */6 * * *",
            sync_mode="incremental",
        )
        fire = self.scheduler.fire(schedule_id=sched["schedule_id"])

        ai1 = self.ai.assist(action="analyze_api", subject="Stripe OpenAPI")
        ai2 = self.ai.assist(action="build_mapping", subject="CRM↔ERP customer")
        ai3 = self.ai.assist(action="optimize", subject="Kafka consumer lag")
        ai4 = self.ai.assist(action="detect_errors", subject="PrivatBank SOAP")
        ai5 = self.ai.assist(action="create_template", subject="Bank connector")

        dash_m = self.dashboard.render(dashboard_type="monitoring")
        dash_r = self.dashboard.render(dashboard_type="registry")
        dash_s = self.dashboard.render(dashboard_type="sync")
        dash_c = self.dashboard.render(dashboard_type="connectors")
        dash_a = self.dashboard.render(dashboard_type="analytics")

        # stop one for lifecycle coverage then leave others running
        stop_kafka = self.manager.stop(integration_id=kafka["integration_id"])

        return {
            "bootstrap": True,
            "integration_telegram_id": tg["integration_id"],
            "integration_stripe_id": stripe["integration_id"],
            "integration_monobank_id": mono["integration_id"],
            "integration_privatbank_id": privat["integration_id"],
            "integration_drive_id": drive["integration_id"],
            "integration_openai_id": openai["integration_id"],
            "integration_anthropic_id": anthropic["integration_id"],
            "integration_kafka_id": kafka["integration_id"],
            "start_telegram_id": start_tg["op_id"],
            "start_stripe_id": start_stripe["op_id"],
            "update_openai_id": upd["op_id"],
            "journal_id": journal["journal_id"],
            "connector_rest_id": rest["call_id"],
            "connector_graphql_id": gql["call_id"],
            "connector_websocket_id": ws["call_id"],
            "adapter_telegram_id": adp_tg["call_id"],
            "adapter_binance_id": adp_bin["call_id"],
            "sync_stripe_id": sync["sync_id"],
            "sync_monobank_id": sync2["sync_id"],
            "retry_id": retry["retry_id"],
            "mapping_id": mapped["mapping_id"],
            "transform_id": xf["transform_id"],
            "validation_id": val["validation_id"],
            "security_oauth_id": sec["security_id"],
            "security_rotate_id": rot["security_id"],
            "security_api_key_id": sec_jwt["security_id"],
            "monitor_telegram_id": mon["monitor_id"],
            "monitor_stripe_id": mon2["monitor_id"],
            "schedule_id": sched["schedule_id"],
            "fire_id": fire["fire_id"],
            "ai_analyze_id": ai1["assist_id"],
            "ai_mapping_id": ai2["assist_id"],
            "ai_optimize_id": ai3["assist_id"],
            "ai_errors_id": ai4["assist_id"],
            "ai_template_id": ai5["assist_id"],
            "dashboard_monitoring_id": dash_m["dashboard_id"],
            "dashboard_registry_id": dash_r["dashboard_id"],
            "dashboard_sync_id": dash_s["dashboard_id"],
            "dashboard_connectors_id": dash_c["dashboard_id"],
            "dashboard_analytics_id": dash_a["dashboard_id"],
            "stop_kafka_id": stop_kafka["op_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "manager": self.manager.status(),
            "registry": self.registry.status(),
            "engine": self.engine.status(),
            "monitor": self.monitor.status(),
            "scheduler": self.scheduler.status(),
            "security": self.security.status(),
            "mapper": self.mapper.status(),
            "transformer": self.transformer.status(),
            "validator": self.validator.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
        }


eip = IntegrationPlatformSuite()
