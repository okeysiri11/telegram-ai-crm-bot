# Multi-Tenant Foundation v1 isolation tests.

from __future__ import annotations

import asyncio
import uuid

from config import OWNER_ID
from database.session import get_session
from repositories.car_repository import CarRepository
from repositories.partner_tenant_repository import TenantUserRoleRepository
from services.pg_car_engine import CarEngineV1
from services.pg_multi_tenant_foundation_engine import MultiTenantFoundationEngineV1
from services.pg_partner_tenant_engine import PartnerTenantEngineV1
from services.tenant_context import TenantContextService


async def _ensure_company_id() -> uuid.UUID:
    from sqlalchemy import select

    from database.models.multi_company import Company

    async with get_session() as session:
        result = await session.execute(select(Company).limit(1))
        company = result.scalar_one_or_none()
        if company is None:
            raise RuntimeError("No company found for tenant isolation test")
        return company.id


async def _create_isolated_tenant(user_id: int, suffix: str) -> uuid.UUID:
    company_id = await _ensure_company_id()
    tenant = await PartnerTenantEngineV1.create_tenant(
        OWNER_ID,
        company_id=company_id,
        code=f"ISO_{suffix}_{user_id}",
        name=f"Isolation Tenant {suffix}",
        provision_billing=False,
    )
    tenant_id = uuid.UUID(tenant["tenant_id"])
    await MultiTenantFoundationEngineV1.sync_tenant_from_partner(
        tenant_id=tenant_id,
        company_id=company_id,
        code=tenant["code"],
        name=tenant["name"],
        member_user_id=user_id,
    )
    return tenant_id


async def run_tenant_isolation_test() -> dict:
    user_a = 910_001
    user_b = 910_002
    vin = f"ISO{uuid.uuid4().hex[:13].upper()}"

    tenant_a = await _create_isolated_tenant(user_a, "A")
    tenant_b = await _create_isolated_tenant(user_b, "B")

    TenantContextService.set_active_tenant(user_a, tenant_a)
    car_a = await CarEngineV1.create_car(
        user_a,
        vin=vin,
        make="Toyota",
        model="Camry",
        year=2022,
    )

    TenantContextService.set_active_tenant(user_b, tenant_b)
    cars_b_before = await CarEngineV1.list_cars(user_b, limit=50)
    leak_b = [c for c in cars_b_before if c.get("id") == car_a.get("id")]

    TenantContextService.set_active_tenant(user_a, tenant_a)
    cars_a = await CarEngineV1.list_cars(user_a, limit=50)
    found_a = any(c.get("id") == car_a.get("id") for c in cars_a)

    async with get_session() as session:
        repo = CarRepository(session)
        cross = await repo.get_by_vin(vin, tenant_id=tenant_b)

    ok = found_a and not leak_b and cross is None
    return {
        "ok": ok,
        "tenant_a": str(tenant_a),
        "tenant_b": str(tenant_b),
        "car_id": car_a.get("id"),
        "tenant_a_sees_own": found_a,
        "tenant_b_leak": bool(leak_b),
        "tenant_b_cross_lookup": cross is not None,
    }


def run_multi_tenant_isolation_test() -> dict:
    return asyncio.run(run_tenant_isolation_test())
