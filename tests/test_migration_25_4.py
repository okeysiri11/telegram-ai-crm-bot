"""Tests — Enterprise Migration & Disaster Recovery (Sprint 25.4 / v8.4.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_migration.models import (
    BACKUP_KINDS,
    DR_SCENARIOS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    SCHEMA_OPS,
)


ROOT = Path(__file__).resolve().parents[1]
PREFIXES = [
    "/api/enterprise-hub/v1",
    "/api/enterprise-orch/v1",
    "/api/enterprise-kg/v1",
    "/api/enterprise-agents/v1",
    "/api/enterprise-comms/v1",
    "/api/enterprise-workflow/v1",
    "/api/enterprise-eip/v1",
    "/api/enterprise-edp/v1",
    "/api/enterprise-isam/v1",
    "/api/enterprise-obs/v1",
    "/api/enterprise-tenancy/v1",
    "/api/enterprise-aop/v1",
    "/api/enterprise-ats/v1",
    "/api/enterprise-ekp/v1",
    "/api/enterprise-aios/v1",
    "/api/enterprise-evp/v1",
    "/api/enterprise-sdp/v1",
    "/api/enterprise-edf/v1",
    "/api/enterprise-edt/v1",
    "/api/enterprise-esi/v1",
    "/api/enterprise-epm/v1",
    "/api/enterprise-ebc/v1",
    "/api/enterprise-ecc/v1",
    "/api/enterprise-eas/v1",
    "/api/enterprise-edc/v1",
    "/api/enterprise-esh/v1",
    "/api/enterprise-eqa/v1",
    "/api/enterprise-edo/v1",
    "/api/enterprise-epf/v1",
    "/api/enterprise-erl/v1",
    "/api/enterprise-epi/v1",
    "/api/enterprise-aba/v1",
    "/api/enterprise-bos/v1",
    "/api/enterprise-bws/v1",
    "/api/enterprise-bcj/v1",
    "/api/enterprise-amo/v1",
    "/api/enterprise-ech/v1",
    "/api/enterprise-eco/v1",
    "/api/enterprise-cpl/v1",
    "/api/enterprise-eon/v1",
    "/api/enterprise-eoc/v1",
    "/api/enterprise-epr/v1",
    "/api/enterprise-eao/v1",
    "/api/enterprise-wfi/v1",
    "/api/enterprise-ekg/v1",
    "/api/enterprise-pin/v1",
    "/api/enterprise-esl/v1",
    "/api/enterprise-etw/v1",
    "/api/enterprise-eoe/v1",
    "/api/enterprise-est/v1",
    "/api/enterprise-ele/v1",
    "/api/enterprise-aph/v1",
    "/api/enterprise-ees/v1",
    "/api/enterprise-eti/v1",
    "/api/enterprise-epl/v1",
    "/api/enterprise-ece/v1",
]
EMR = "/api/enterprise-emr/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    enterprise_hub.reset()
    yield
    enterprise_hub.reset()


def test_version_emr_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "8.4.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.3.0"
    assert health["migration_platform_ready"] is True
    assert health["backup_manager_ready"] is True
    assert health["rollback_ready"] is True
    assert health["disaster_recovery_ready"] is True
    assert health["engines"]["migration"] == "1.0"
    assert health["chaos_engineering_ready"] is True
    assert "create_table" in SCHEMA_OPS
    assert "secrets" in BACKUP_KINDS
    assert "full_outage_recovery" in DR_SCENARIOS
    assert "chaos_engineering" in INTEGRATION_TARGETS
    assert KPI_TARGETS["no_data_loss"] is True
    assert "backup_before_migrate" in PRINCIPLES


def test_migration_backup_restore_rollback_dr():
    suite = enterprise_hub.migration
    mig = suite.create_migration(
        migration_id="mig_demo",
        version_from="8.3.0",
        version_to="8.4.0",
        module="enterprise_hub",
        author="qa",
    )
    assert mig["rollback_support"] is True
    assert mig["status"] == "pending"

    with pytest.raises(ValidationError):
        suite.create_migration(
            migration_id="mig_unsafe",
            version_from="8.3.0",
            version_to="8.4.0",
            module="x",
            rollback_support=False,
        )

    backups = suite.backup(label="pre")
    assert backups["complete"] is True
    assert backups["count"] == len(BACKUP_KINDS)

    run = suite.run_migration(
        migration_id="mig_demo",
        schema_ops=[{"op": "create_table", "target": "demo"}],
        data_ops=[{"op": "transfer", "records": 5}, {"op": "integrity_check"}],
    )
    assert run["schema"]["all_reversible"] is True
    assert run["data"]["integrity_verified"] is True
    assert run["validation"]["passed"] is True
    assert run["no_data_loss"] is True

    bak_id = backups["backups"][0]["backup_id"]
    restored = suite.restore(target="database", backup_id=bak_id)
    assert restored["restored"] is True
    assert restored["data_loss"] is False

    rolled = suite.rollback(mode="last", migration_id="mig_demo")
    assert rolled["rolled_back"] is True
    assert rolled["safe"] is True

    validation = suite.validate_recovery()
    assert validation["passed"] is True
    assert validation["no_data_loss"] is True

    dr = suite.disaster_test(scenario="database_loss")
    assert dr["validated"] is True
    assert dr["data_loss"] is False

    all_dr = suite.disaster_test(all_scenarios=True)
    assert all_dr["passed"] is True
    assert all_dr["count"] == len(DR_SCENARIOS)

    versions = suite.version_status()
    assert versions["current_version"] == "8.4.0"
    assert versions["rollback_availability"] is True

    dash = suite.dashboard()
    assert dash["ci_cd_required"] is True
    assert dash["current_version"] == "8.4.0"


def test_bootstrap_emr():
    suite = enterprise_hub.migration
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "8.4.0"
    assert boot["migration_platform_ready"] is True
    assert boot["backup_manager_ready"] is True
    assert boot["rollback_ready"] is True
    assert boot["disaster_recovery_ready"] is True
    assert boot["no_data_loss"] is True
    assert boot["all_schema_reversible"] is True
    assert boot["ci_cd_required"] is True
    assert boot["required_before_production"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_emr(client):
    health = await client.get(f"{EMR}/health")
    body = await health.json()
    assert body["application_version"] == "8.4.0"
    assert body["migration_platform_ready"] is True

    boot = await client.post(f"{EMR}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["backup_manager_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "8.4.0"


def test_docs_and_regression_25_4():
    for name in (
        "ENTERPRISE_MIGRATION.md",
        "EMR_MANAGER_SCHEMA_DATA.md",
        "EMR_BACKUP_RESTORE_ROLLBACK.md",
        "EMR_DR_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_MIGRATION.md").exists()
    assert (ROOT / "platform_migration" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "migration" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS_CFG.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert '"application_version": "8.4.0"' in manifest
    assert "25.4" in manifest
