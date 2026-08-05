"""Sprint 35.1 — Foundation Completion tests."""

from __future__ import annotations

import inspect

import pytest

from database.models.calendar import CalendarEvent
from database.models.client_request import ClientRequest
from database.models.deals import Deal
from database.models.lead_engine import LeadEngineLead
from database.models.mixins import VersionColumnsMixin, VersionMixin
from database.models.tasks import Task
from database.models.users import User
from platform_architecture.canonical_services import CANONICAL_SERVICES, canonical_summary
from platform_architecture.service_discovery import platform_service_discovery
from platform_identity.hub_bridge import hub_identity_bridge
from platform_identity.permission_sync import sync_permission_registry
from platform_state.event_store import PlatformEventStore
from platform_state.service import platform_state
from platform_state.version_engine import version_engine


@pytest.fixture(autouse=True)
def _reset():
    platform_state.reset()
    yield
    platform_state.reset()


def test_version_mixin_on_core_entities():
    for model in (Task, CalendarEvent, Deal, LeadEngineLead, ClientRequest, User):
        assert issubclass(model, VersionMixin) or issubclass(model, VersionColumnsMixin), model.__name__
        assert hasattr(model, "version")
        assert hasattr(model, "change_id")
        assert hasattr(model, "source_client")


def test_td54_version_mixin_has_no_string_tenant_collision():
    assert hasattr(VersionMixin, "version")
    assert "tenant_id" not in VersionMixin.__dict__


def test_canonical_registry_foundation_locked():
    for key in (
        "identity_core",
        "platform_registry",
        "platform_state",
        "sync_engine",
        "version_engine",
        "platform_event_store",
        "service_discovery",
    ):
        assert key in CANONICAL_SERVICES
    summary = platform_service_discovery.summary()
    assert summary["foundation_locked"] is True
    assert summary["single_registry"] is True


def test_service_discovery_identity_navigation_permissions():
    ident = platform_service_discovery.identity_registration()
    assert ident["canonical"] == "platform_identity"
    nav = platform_service_discovery.navigation_registration()
    assert nav["sor"].startswith("platform_registry")
    assert nav["menu_count"] > 0
    perms = platform_service_discovery.permission_registration()
    assert "platform_state" in perms["realtime_channels"]
    sync = sync_permission_registry()
    assert sync["canonical"] == "platform_identity"
    assert sync["aligned"] is True


def test_hub_isam_bridge_status():
    status = hub_identity_bridge.status()
    assert status["canonical"] == "platform_identity"
    assert status["rewrites_hub_auth"] is False


def test_jsonl_event_store_compatible():
    store = PlatformEventStore(memory=True)
    a = store.append(event_type="TaskCreated", entity_type="task", entity_id="1", payload={"ok": True})
    b = store.append(event_type="TaskUpdated", entity_type="task", entity_id="1", version=2)
    assert a.seq < b.seq
    assert store.count() == 2
    assert store.stream("task", "1")[0].event_id == a.event_id


def test_ha_version_warm_start_and_checkpoint(tmp_path, monkeypatch):
    heads = tmp_path / "heads.jsonl"
    monkeypatch.setenv("ADOS_VERSION_HEADS", str(heads))
    monkeypatch.setenv("ADOS_EVENT_STORE_MEMORY", "0")
    ent = version_engine.create(entity_type="lead", data={"n": 1}, created_by="u", source_client="web")
    path = version_engine.checkpoint_heads(str(heads))
    assert path
    version_engine.reset()
    assert version_engine.get("lead", ent.id) is None
    loaded = version_engine.load_checkpoint(str(heads))
    assert loaded >= 1
    warm = version_engine.warm_start()
    assert warm["warm_started"] is True
    assert version_engine.status()["ha"]


def test_enterprise_foundation_locked_flag():
    status = platform_state.enterprise.status()
    assert status["foundation_locked"] is True
    assert status["foundation_sprint"] == "35.1"


def test_backward_compat_34_2_stack():
    # Smoke: prior sprint surfaces still present
    assert platform_state.status()["unified_platform_state"] is True
    assert platform_state.status()["enterprise_runtime"] is True
    from platform_registry.service import platform_registry

    snap = platform_registry.snapshot()
    assert snap["sprint"] == "34.2B"
    from platform_identity.identity_service import identity_service

    assert identity_service.status()["sprint"] == "34.2A"
