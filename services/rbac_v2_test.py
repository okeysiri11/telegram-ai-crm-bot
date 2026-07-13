# RBAC v2 tests — access matrix and tenant isolation.

from __future__ import annotations

import asyncio

from config import OWNER_ID
from database.session import get_session
from repositories.rbac_v2_repository import RbacV2Repository
from services.multi_tenant_isolation_test import run_tenant_isolation_test
from services.rbac_v2 import RbacV2Engine


async def _setup_test_user(user_id: int, role_code: str) -> None:
    async with get_session() as session:
        repo = RbacV2Repository(session)
        await repo.clear_user_roles(user_id)
        await repo.assign_role_by_code(user_id, role_code)
    RbacV2Engine.invalidate_cache(user_id)


async def run_access_matrix_test() -> dict:
    await RbacV2Engine.seed_defaults()
    matrix = await RbacV2Engine.get_access_matrix()

    checks = {
        "OWNER_has_billing_approve": matrix["OWNER"].get("billing.approve", False),
        "AUTO_OPERATOR_has_auto_car_write": matrix["AUTO_OPERATOR"].get("auto.car.write", False),
        "AUTO_OPERATOR_no_billing_approve": not matrix["AUTO_OPERATOR"].get("billing.approve", True),
        "CLIENT_MANAGER_has_tenant_isolated": matrix["CLIENT_MANAGER"].get("tenant.isolated", False),
        "FINANCE_MANAGER_has_analytics_export": matrix["FINANCE_MANAGER"].get("analytics.export", False),
        "LAW_MANAGER_no_auto_module": not matrix["LAW_MANAGER"].get("auto.module", True),
        "SUPER_MANAGER_inherits_auto": matrix["SUPER_MANAGER"].get("auto.car.write", False),
    }

    user_a = 920_001
    user_b = 920_002
    await _setup_test_user(user_a, "AUTO_OWNER")
    await _setup_test_user(user_b, "CLIENT_MANAGER")

    owner_perms = await RbacV2Engine.get_effective_permissions(user_a)
    client_perms = await RbacV2Engine.get_effective_permissions(user_b)

    user_mgr = 920_003
    await _setup_test_user(user_mgr, "AUTO_MANAGER")
    mgr_perms = await RbacV2Engine.get_effective_permissions(user_mgr)

    runtime_checks = {
        "auto_owner_billing_manage": "billing.manage" in owner_perms,
        "client_manager_no_billing_manage": "billing.manage" not in client_perms,
        "client_manager_tenant_isolated": "tenant.isolated" in client_perms,
        "inheritance_auto_manager_gets_operator": "auto.car.read" in mgr_perms,
    }

    ok = all(checks.values()) and all(runtime_checks.values())
    return {
        "ok": ok,
        "matrix_roles": len(matrix),
        "checks": checks,
        "runtime_checks": runtime_checks,
    }


async def run_tenant_isolation_rbac_test() -> dict:
    user_a = 920_101
    user_b = 920_102
    await _setup_test_user(user_a, "AUTO_OWNER")
    await _setup_test_user(user_b, "CLIENT_OWNER")

    a_can = await RbacV2Engine.has_permission(user_a, "tenant.isolated")
    b_can = await RbacV2Engine.has_permission(user_b, "tenant.isolated")
    a_admin = await RbacV2Engine.has_tenant_access(user_a, write=True)
    b_admin = await RbacV2Engine.has_tenant_access(user_b, write=True)

    isolation = await run_tenant_isolation_test()

    ok = a_can and b_can and a_admin and b_admin and isolation.get("ok", False)
    return {
        "ok": ok,
        "rbac_tenant_isolated_a": a_can,
        "rbac_tenant_isolated_b": b_can,
        "data_isolation": isolation,
    }


async def run_rbac_v2_test_suite() -> dict:
    await RbacV2Engine.seed_defaults()
    matrix_result = await run_access_matrix_test()
    tenant_result = await run_tenant_isolation_rbac_test()
    owner_bypass = await RbacV2Engine.has_permission(OWNER_ID, "billing.approve")
    return {
        "ok": matrix_result.get("ok") and tenant_result.get("ok") and owner_bypass,
        "access_matrix": matrix_result,
        "tenant_isolation": tenant_result,
        "owner_bypass": owner_bypass,
    }


def run_rbac_v2_tests() -> dict:
    return asyncio.run(run_rbac_v2_test_suite())
