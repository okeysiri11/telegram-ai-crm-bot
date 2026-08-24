"""AUTO Enterprise — private import OS (Sprint AUTO 1.0)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AutoEnterpriseConfig:
    application_name: str = "Auto Import Operating System"
    application: str = "auto_enterprise"
    application_version: str = "1.8.5"
    api_prefix: str = "/api/auto-ops/v1"
    sprint: str = "AUTO_1.8.5"


DEFAULT_CONFIG = AutoEnterpriseConfig()
