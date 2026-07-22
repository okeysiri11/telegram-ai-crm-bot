# Port ERP configuration — Sprint 9.8 Global Network & Production Release.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortERPConfig:
    application_name: str = "Port ERP"
    application_version: str = "2.0.0"
    platform_dependency: str = "AI Platform Core v3"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/port/v1"
    internal_prefix: str = "/internal/port/v1"
    webhook_prefix: str = "/webhooks/port/v1"
    default_currency: str = "USD"
    port_core: str = "1.0"
    tracking_engine: str = "1.0"
    terminal_engine: str = "1.0"
    customs_engine: str = "1.0"
    logistics_engine: str = "1.0"
    ai_operations_engine: str = "1.0"
    finance_engine: str = "1.0"
    enterprise_engine: str = "1.0"
    global_network: str = "1.0"


DEFAULT_CONFIG = PortERPConfig()
