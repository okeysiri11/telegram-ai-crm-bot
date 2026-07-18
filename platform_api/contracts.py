# Frozen API contract metadata — Platform v1.0 API Freeze.

from __future__ import annotations

from pydantic import BaseModel, Field

PLATFORM_API_VERSION = "v1"
API_CONTRACT_VERSION = "1.0.0"
API_FREEZE_DATE = "2026-07-18"


class ContractInfo(BaseModel):
    api_version: str = PLATFORM_API_VERSION
    contract_version: str = API_CONTRACT_VERSION
    freeze_date: str = API_FREEZE_DATE


class SystemInfoData(BaseModel):
    platform_version: str = ""
    build_version: str = ""
    git_revision: str = ""
    environment: str = ""
    uptime_seconds: float = 0.0


class HealthSnapshotData(BaseModel):
    overall_status: str = "unknown"


class AuditSearchData(BaseModel):
    entries: list[dict] = Field(default_factory=list)
    count: int = 0
    pagination: dict | None = None
