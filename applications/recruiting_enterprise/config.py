# Recruiting Ops — Sprint Recruiting 1.0.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecruitingEnterpriseConfig:
    application_name: str = "Recruiting Operations"
    application: str = "recruiting_enterprise"
    application_version: str = "1.0.0"
    api_prefix: str = "/api/recruiting-ops/v1"
    sprint: str = "recruiting_1.0"


DEFAULT_CONFIG = RecruitingEnterpriseConfig()
