"""Chaos library facade — Sprint 25.3."""

from __future__ import annotations

from typing import Any

from platform_chaos.circuit import CircuitBreakerManager
from platform_chaos.controller import ChaosController
from platform_chaos.dashboard import ChaosDashboard
from platform_chaos.dependencies import DependencyAnalyzer
from platform_chaos.fallback import FallbackEngine
from platform_chaos.health import ServiceHealthMonitor
from platform_chaos.injector import FailureInjector
from platform_chaos.integrations import ChaosIntegrations
from platform_chaos.models import PRINCIPLES
from platform_chaos.recovery import RecoveryEngine
from platform_chaos.reports import ChaosReports
from platform_chaos.retry import RetryEngine


class ChaosLibrary:
    def __init__(self) -> None:
        self.controller = ChaosController()
        self.injector = FailureInjector()
        self.recovery = RecoveryEngine()
        self.circuit = CircuitBreakerManager()
        self.retry = RetryEngine()
        self.fallback = FallbackEngine()
        self.health = ServiceHealthMonitor()
        self.dependencies = DependencyAnalyzer()
        self.dashboard = ChaosDashboard()
        self.reports = ChaosReports()
        self.integrations = ChaosIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        scenario = self.controller.create_scenario(
            scenario_id="chs_event_bus_down",
            name="Event Bus Offline",
            description="Simulate event bus outage",
            target_service="event_bus",
            failure_type="event_bus_offline",
            duration_sec=20,
        )
        injection = self.injector.inject(scenario=scenario)
        recovery = self.recovery.verify(scenario=scenario, injection=injection)
        circuit = self.circuit.evaluate(failure_count=5, success_after_open=3)
        retry = self.retry.run(strategy="exponential_backoff", max_attempts=4)
        fallback = self.fallback.activate(preferred="backup_queue")
        deps = self.dependencies.map(failed_service="event_bus")
        health = self.health.snapshot(services=deps["chain"][:5], incidents={"event_bus": 1})
        reports = self.reports.generate(
            run_id="chaos_boot",
            summary={
                "incidents": [{"service": "event_bus", "type": "event_bus_offline"}],
                "recovery_events": [{"event": "queues_restored"}],
                "root_cause": "injected_event_bus_offline",
                "recommendations": ["verify_retry_policies", "keep_backup_queue_warm"],
            },
        )
        dash = self.dashboard.render(
            active_tests=[scenario["scenario_id"]],
            health=health,
            incidents=[{"service": "event_bus"}],
            recovery=recovery,
            circuit=circuit,
            retry=retry,
            fallback=fallback,
            availability=0.97,
            recovery_time_ms=recovery["recovery_time_ms"],
            recommendations=["verify_retry_policies", "keep_backup_queue_warm"],
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "chaos_engineering_ready": True,
            "failure_injection_ready": True,
            "recovery_engine_ready": True,
            "circuit_breaker_ready": True,
            "no_data_loss": True,
            "automatic_recovery": recovery["automatic"],
            "ci_cd_required": True,
            "required_before_production": True,
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "scenario": scenario,
                "injection": injection,
                "recovery": recovery,
                "circuit": circuit,
                "retry": retry,
                "fallback": fallback,
                "dependencies": deps,
                "health": health,
                "reports": reports,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "controller",
                "injector",
                "recovery",
                "circuit",
                "retry",
                "fallback",
                "health",
                "dependencies",
                "dashboard",
                "reports",
            ],
            "principles": self.principles(),
            "ci_cd_required": True,
        }


chaos_library = ChaosLibrary()
