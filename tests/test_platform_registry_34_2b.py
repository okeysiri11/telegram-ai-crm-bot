"""Sprint 34.2B — Unified Platform Registry tests."""

from __future__ import annotations

import pytest

from platform_registry.agents import all_agents
from platform_registry.menus import MENU_CATALOG, menu_item_by_id
from platform_registry.navigation import filter_menu, group_menu
from platform_registry.permissions import permissions_for_roles
from platform_registry.roles import all_platform_roles, role_title
from platform_registry.service import platform_registry
from platform_registry.verticals import all_verticals
from platform_registry.visibility import ClientId
from platform_registry.workspaces import all_workspace_modules


def test_snapshot_has_all_catalogs():
    snap = platform_registry.snapshot()
    assert snap["sprint"] == "34.2B"
    assert snap["menu_count"] == len(MENU_CATALOG)
    assert len(snap["roles"]) >= 10
    assert len(snap["permissions"]) >= 10
    assert len(snap["verticals"]) >= 10
    assert len(snap["workspaces"]) >= 10
    assert len(snap["agents"]) >= 8
    assert len(snap["routes"]) > 0


def test_role_titles():
    codes = {r.code for r in all_platform_roles()}
    assert "owner" in codes
    assert role_title("OWNER") == "Platform Owner"
    assert role_title("ceo") == "Company Owner"


@pytest.mark.parametrize(
    "role",
    ["owner", "manager", "employee", "partner", "dealer", "client", "guest"],
)
def test_permissions_identical_vocabulary(role: str):
    perms = permissions_for_roles([role])
    assert isinstance(perms, list)
    if role == "guest":
        assert "knowledge.read" in perms
    if role == "owner":
        assert "owner.full_access" in perms or "crm.write" in perms


@pytest.mark.parametrize("client", ["web", "telegram", "desktop", "mobile"])
@pytest.mark.parametrize("role", ["owner", "manager", "employee", "client", "guest"])
def test_navigation_per_client_role(client: str, role: str):
    data = platform_registry.navigation_for(
        client=client,
        roles=[role],
        include_owner=role in {"owner", "ceo"},
        simple=False,
    )
    assert data["client"] == client
    assert "groups" in data
    assert "items" in data
    # Owner sees owner group items on interactive clients
    if role == "owner" and client in {"web", "telegram", "desktop"}:
        ids = {i["id"] for i in data["items"]}
        assert "ws_home" in ids or "biz_crm" in ids or "vert_crypto" in ids


def test_web_and_telegram_owner_share_crm_route():
    web = platform_registry.navigation_for(client="web", roles=["owner"], include_owner=True)
    tg = platform_registry.navigation_for(client="telegram", roles=["owner"], include_owner=True)
    web_crm = next((i for i in web["items"] if i["id"] == "biz_crm"), None)
    tg_crm = next((i for i in tg["items"] if i["id"] == "biz_crm"), None)
    assert web_crm is not None and tg_crm is not None
    assert web_crm["route"] == tg_crm["route"] == "/crm"


def test_filter_menu_hides_owner_for_client():
    items = filter_menu(client=ClientId.WEB.value, roles=["client"], include_owner=False)
    assert all(not i.owner_only for i in items)


def test_casino_is_first_class_web_entry():
    item = menu_item_by_id("vert_casino")
    assert item is not None
    assert item.route == "/casino"
    assert item.title == "Casino"
    web = platform_registry.navigation_for(client="web", roles=["owner"], include_owner=True, simple=False)
    casino = next((i for i in web["items"] if i["id"] == "vert_casino"), None)
    assert casino is not None
    assert casino["route"] == "/casino"


def test_group_menu_structure():
    items = filter_menu(client="web", roles=["owner"], include_owner=True)
    groups = group_menu(items)
    assert any(g["id"] == "workspace" for g in groups)


def test_verticals_include_future_and_core():
    ids = {v.id for v in all_verticals()}
    assert "company_core" in ids
    assert "crypto_otc" in ids
    assert "ai_marketplace" in ids
    assert "medical" in ids


def test_workspace_modules_core_set():
    ids = {w.id for w in all_workspace_modules()}
    for required in ("crm", "erp", "calendar", "tasks", "knowledge", "desktop"):
        assert required in ids


def test_agents_have_clients_and_permissions():
    for agent in all_agents():
        assert agent.available_clients
        assert agent.permissions


def test_telegram_adapter_rows():
    from platform_registry.clients.telegram_adapter import telegram_menu_rows

    rows = telegram_menu_rows(roles=["owner"], include_owner=True)
    flat = [c for row in rows for c in row]
    assert any("Crypto" in c or "Календарь" in c or "AI" in c for c in flat)
