"""AUTO 1.0 repository — Postgres persist with memory-friendly dicts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.auto_ops import (
    AutoOpsAudit,
    AutoOpsBroker,
    AutoOpsCarrier,
    AutoOpsClient,
    AutoOpsContainer,
    AutoOpsContainerVehicle,
    AutoOpsCustomsCase,
    AutoOpsCustomsSetting,
    AutoOpsDeal,
    AutoOpsDocument,
    AutoOpsDocumentTemplate,
    AutoOpsDriver,
    AutoOpsExpense,
    AutoOpsFile,
    AutoOpsLogisticsEvent,
    AutoOpsLogisticsSetting,
    AutoOpsNotification,
    AutoOpsPhoto,
    AutoOpsPort,
    AutoOpsReceipt,
    AutoOpsReservation,
    AutoOpsSale,
    AutoOpsShipment,
    AutoOpsTask,
    AutoOpsTelegramMember,
    AutoOpsTelegramOutbox,
    AutoOpsTruck,
    AutoOpsVehicle,
    AutoOpsVessel,
    AutoOpsStatusHistory,
    AutoOpsFinanceAccount,
)

KIND_MODEL = {
    "vehicle": AutoOpsVehicle,
    "expense": AutoOpsExpense,
    "document": AutoOpsDocument,
    "document_template": AutoOpsDocumentTemplate,
    "photo": AutoOpsPhoto,
    "client": AutoOpsClient,
    "task": AutoOpsTask,
    "audit": AutoOpsAudit,
    "file": AutoOpsFile,
    "shipment": AutoOpsShipment,
    "carrier": AutoOpsCarrier,
    "driver": AutoOpsDriver,
    "truck": AutoOpsTruck,
    "container": AutoOpsContainer,
    "container_vehicle": AutoOpsContainerVehicle,
    "vessel": AutoOpsVessel,
    "port": AutoOpsPort,
    "logistics_event": AutoOpsLogisticsEvent,
    "notification": AutoOpsNotification,
    "logistics_setting": AutoOpsLogisticsSetting,
    "customs_case": AutoOpsCustomsCase,
    "broker": AutoOpsBroker,
    "customs_setting": AutoOpsCustomsSetting,
    "deal": AutoOpsDeal,
    "reservation": AutoOpsReservation,
    "sale": AutoOpsSale,
    "receipt": AutoOpsReceipt,
    "telegram_member": AutoOpsTelegramMember,
    "telegram_outbox": AutoOpsTelegramOutbox,
    "status_history": AutoOpsStatusHistory,
    "finance_account": AutoOpsFinanceAccount,
}


def _uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except Exception:
        return None


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def row_to_dict(row: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"id": str(row.id)}
    for col in row.__table__.columns:
        if col.name == "id":
            continue
        val = getattr(row, col.name, None)
        if isinstance(val, datetime):
            out[col.name] = val.isoformat()
        elif isinstance(val, UUID):
            out[col.name] = str(val)
        elif isinstance(val, Decimal):
            out[col.name] = float(val)
        else:
            out[col.name] = val
    return out


class AutoOpsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(self, kind: str, data: dict[str, Any]) -> Any:
        model = KIND_MODEL[kind]
        cols = {c.name for c in model.__table__.columns}
        payload = {k: v for k, v in data.items() if k in cols}
        if "id" in payload:
            uid = _uuid(str(payload["id"]))
            if uid:
                payload["id"] = uid
            else:
                payload.pop("id", None)
        for key in ("amount", "exchange_rate", "amount_base_currency", "purchase_price", "buyer_fee", "estimated_market_value", "mileage", "sale_price_expected", "sale_price_actual", "customs_value", "fx_rate_to_uah", "engine_cc", "broker_fee_uah", "duty_uah", "excise_uah", "import_vat_uah", "state_total_uah", "grand_total_uah", "price", "sale_price", "balance"):
            if key in payload:
                payload[key] = _decimal(payload[key])
        row = model(**payload)
        self._session.add(row)
        await self._session.flush()
        return row

    async def update(self, kind: str, item_id: str, patch: dict[str, Any]) -> Any | None:
        model = KIND_MODEL[kind]
        uid = _uuid(item_id)
        if not uid:
            return None
        row = await self._session.get(model, uid)
        if row is None:
            return None
        cols = {c.name for c in model.__table__.columns}
        for key, val in patch.items():
            if key in {"id", "organization_id", "created_at"}:
                continue
            if key not in cols:
                continue
            if key in ("amount", "exchange_rate", "amount_base_currency", "purchase_price", "buyer_fee", "estimated_market_value", "mileage", "sale_price_expected", "sale_price_actual", "customs_value", "fx_rate_to_uah", "engine_cc", "broker_fee_uah", "duty_uah", "excise_uah", "import_vat_uah", "state_total_uah", "grand_total_uah", "price", "sale_price"):
                val = _decimal(val)
            setattr(row, key, val)
        await self._session.flush()
        return row

    async def delete(self, kind: str, item_id: str) -> bool:
        model = KIND_MODEL[kind]
        uid = _uuid(item_id)
        if not uid:
            return False
        row = await self._session.get(model, uid)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def list_kind(self, kind: str, organization_id: str, *, limit: int = 500) -> list[Any]:
        model = KIND_MODEL[kind]
        q = (
            select(model)
            .where(model.organization_id == organization_id)
            .order_by(model.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())
