# Unit tests for role-based vertical CRM routing (no DB required for enums/access).

from __future__ import annotations


def test_system_roles_defined() -> None:
    from services.system_roles import SYSTEM_ROLE_CODES, SystemRole

    assert SystemRole.SUPER_ADMIN.value == "SUPER_ADMIN"
    assert SystemRole.AUTO_MANAGER.value == "AUTO_MANAGER"
    assert SystemRole.AGRO_MANAGER.value == "AGRO_MANAGER"
    assert SystemRole.CLIENT.value == "CLIENT"
    assert SYSTEM_ROLE_CODES == {
        "SUPER_ADMIN",
        "AUTO_MANAGER",
        "AGRO_MANAGER",
        "CLIENT",
    }


def test_verticals_and_aliases() -> None:
    from services.system_roles import Vertical, normalize_vertical

    assert normalize_vertical("AUTO") == "auto"
    assert normalize_vertical("auto_client") == "auto"
    assert normalize_vertical("agro_trading") == "agro"
    assert Vertical.REALTY.value == "realty"
    assert Vertical.LOGISTICS.value == "logistics"


def test_manager_statuses() -> None:
    from services.system_roles import MANAGER_LEAD_STATUSES, ManagerLeadStatus

    for code in (
        "NEW",
        "TAKEN",
        "IN_PROGRESS",
        "WAITING_CLIENT",
        "DEAL",
        "CLOSED",
        "REJECTED",
    ):
        assert code in MANAGER_LEAD_STATUSES
    assert ManagerLeadStatus.TAKEN.value == "TAKEN"


def test_access_matrix() -> None:
    from services.system_roles import SystemRole, role_has_access

    assert role_has_access(SystemRole.SUPER_ADMIN, "admin_panel")
    assert role_has_access(SystemRole.SUPER_ADMIN, "reassign_leads")
    assert not role_has_access(SystemRole.CLIENT, "admin_panel")
    assert role_has_access(SystemRole.AUTO_MANAGER, "auto_leads")
    assert role_has_access(SystemRole.AGRO_MANAGER, "agro_leads")
    assert not role_has_access(SystemRole.CLIENT, "manager_crm")


def test_role_default_verticals() -> None:
    from services.system_roles import ROLE_DEFAULT_VERTICALS, SystemRole

    assert ROLE_DEFAULT_VERTICALS[SystemRole.AUTO_MANAGER.value] == ("auto",)
    assert ROLE_DEFAULT_VERTICALS[SystemRole.AGRO_MANAGER.value] == ("agro",)
    assert "auto" in ROLE_DEFAULT_VERTICALS[SystemRole.SUPER_ADMIN.value]
    assert ROLE_DEFAULT_VERTICALS[SystemRole.CLIENT.value] == ()


def test_super_admin_menu_buttons() -> None:
    from keyboards import super_admin_menu

    texts = {btn.text for row in super_admin_menu().keyboard for btn in row}
    required = {
        "🏢 Авто",
        "🌾 Агро",
        "🏠 Недвижимость",
        "🚛 Логистика",
        "👥 Пользователи",
        "📋 Все заявки",
        "📊 Аналитика",
        "💰 Финансы",
        "⚙️ Настройки",
        "🤖 AI Центр управления",
    }
    assert required.issubset(texts)


def test_routing_engine_importable() -> None:
    from services.pg_vertical_routing_engine import VerticalRoutingEngineV1

    assert hasattr(VerticalRoutingEngineV1, "resolve_manager_for_vertical")
    assert hasattr(VerticalRoutingEngineV1, "ensure_platform_actors")


def test_user_model_has_role_verticals() -> None:
    from database.models.users import User

    assert hasattr(User, "role")
    assert hasattr(User, "verticals")


def test_subscription_model_exists() -> None:
    from database.models.manager_vertical_subscription import ManagerVerticalSubscription

    assert ManagerVerticalSubscription.__tablename__ == "manager_vertical_subscriptions_v1"


def main() -> None:
    test_system_roles_defined()
    test_verticals_and_aliases()
    test_manager_statuses()
    test_access_matrix()
    test_role_default_verticals()
    test_super_admin_menu_buttons()
    test_routing_engine_importable()
    test_user_model_has_role_verticals()
    test_subscription_model_exists()
    print("vertical_crm_routing: OK")


if __name__ == "__main__":
    main()
