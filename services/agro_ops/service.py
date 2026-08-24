"""AGRO Ops service — durable agribusiness desk (AGRO Production 1.0).

Mirrors the Legal Ops pattern: org-scoped in-memory bags hydrated from and
persisted to Postgres (generic `agro_ops_records` registry). Memory keeps
working when the DB is unreachable; nothing is faked — external data stays
NOT_CONFIGURED until a real provider is connected.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from repositories.agro_ops_repository import AgroOpsRepository, record_to_dict
from services.agro_ops.analysts import AgroOpsAnalystMixin
from services.agro_ops.analytics import AgroOpsAnalyticsMixin
from services.agro_ops.command_center import AgroOpsCommandCenterMixin
from services.agro_ops.crm import AgroOpsCrmMixin
from services.agro_ops.operations import AgroOpsLifecycleMixin
from services.agro_ops.production import AgroOpsProductionMixin
from services.agro_ops.production_26 import AgroOpsProduction26Mixin, PROD26_VERSION
from services.agro_ops.desk import AgroOpsDeskMixin
from services.agro_ops.desk_settings import AgroOpsDeskSettingsMixin
from services.agro_ops.finance import AgroOpsFinanceMixin
from services.agro_ops.intelligence import AgroOpsIntelMixin
from services.agro_ops.logistics import AgroOpsLogisticsMixin
from services.agro_ops.markets import AgroOpsMarketsMixin
from services.agro_ops.providers import AgroOpsProviderMixin
from services.agro_ops.rbac import can, normalize_role, require, roles_catalog
from services.agro_ops.warehouses import AgroOpsWarehouseMixin
from services.agro_ops.weather import AgroOpsWeatherMixin

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Catalog metadata (labels only; data itself is user-created, never invented)
# ---------------------------------------------------------------------------

COUNTERPARTY_TYPES = [
    ("farmer", "Фермер / хозяйство"),
    ("farm", "Фермер / хозяйство"),
    ("producer", "Производитель"),
    ("trader", "Трейдер"),
    ("elevator", "Элеватор"),
    ("warehouse", "Склад"),
    ("processor", "Переработчик"),
    ("plant", "Завод"),
    ("exporter", "Экспортёр"),
    ("importer", "Импортёр"),
    ("carrier", "Перевозчик"),
    ("forwarder", "Экспедитор"),
    ("broker", "Брокер"),
    ("port", "Порт / терминал"),
    ("supplier", "Поставщик"),
    ("buyer", "Покупатель"),
    ("agro_company", "Агрокомпания"),
    ("bank", "Банк"),
    ("insurance", "Страховая компания"),
    ("counterparty", "Контрагент"),
    ("other", "Другое"),
]

COUNTERPARTY_STATUSES = [
    ("lead", "Новый"),
    ("new", "Новый"),
    ("active", "Активный"),
    ("negotiation", "Переговоры"),
    ("review", "На проверке"),
    ("on_hold", "Приостановлен"),
    ("risk", "Проблемный"),
    ("problem", "Проблемный"),
    ("blocked", "Чёрный список"),
    ("blacklist", "Чёрный список"),
    ("archived", "Архив"),
]

DEAL_STATUSES = [
    ("draft", "Новая"),
    ("negotiation", "Переговоры"),
    ("approved", "Согласование"),
    ("awaiting_contract", "Ожидает договор"),
    ("contracted", "Договор подписан"),
    ("awaiting_payment", "Ожидает оплату"),
    ("paid_partly", "Оплачено частично"),
    ("paid", "Оплачено"),
    ("in_delivery", "В поставке"),
    ("delivered", "Получено / передано"),
    ("closed", "Закрыта"),
    ("problem", "Проблема"),
    ("cancelled", "Отменена"),
]

DEFAULT_CROPS = [
    "Пшеница", "Кукуруза", "Ячмень", "Подсолнечник", "Рапс",
    "Соя", "Горох", "Масло подсолнечное", "Шрот", "Жмых",
]

DEFAULT_CURRENCIES = ["UAH", "USD", "EUR"]
DEFAULT_UNITS = ["т", "кг", "л", "шт"]

# Kinds stored in the durable registry
KINDS = {
    "counterparty", "contact", "crop", "deal", "contract", "document", "file",
    "calculation", "invoice", "payment", "shipment", "warehouse", "task",
    "calendar", "market", "intel_source", "report", "notification", "settings",
    "activity",
    "carrier", "vehicle", "trailer", "driver", "trip",
    "market_price", "storage_unit", "inventory_lot", "warehouse_operation",
    "provider_snapshot", "market_observation", "trade_observation",
    "weather_observation", "crop_observation", "price_observation",
    "availability", "demand",     "alert_rule", "alert", "delivery_leg",
    "provider_raw", "analyst_output",
    "communication", "note", "bank_account",
    "agro_operation", "weighing", "quality_test", "stock_movement", "expense", "ops_exception", "truck_run",
    "agro_field", "crop_season", "field_work", "machine", "implement", "material", "material_movement",
    "maintenance", "harvest_plan", "harvest_actual", "field_cost", "field_issue",
    "agro_crop",
}

SYSTEM_KINDS = {
    "provider_snapshot", "market_observation", "trade_observation",
    "weather_observation", "crop_observation", "price_observation",
    "provider_raw", "analyst_output",
}

# Which RBAC action is needed to create/update a kind (default: create/edit)
FINANCE_KINDS = {"calculation", "invoice", "payment", "bank_account", "expense", "field_cost"}

REQUIRED_FIELD = {
    "counterparty": ("name", "Укажите название контрагента"),
    "contact": ("full_name", "Укажите ФИО контактного лица"),
    "crop": ("name", "Укажите название культуры / продукта"),
    "deal": ("title", "Укажите название сделки"),
    "contract": ("title", "Укажите название договора"),
    "document": ("title", "Укажите название документа"),
    "calculation": ("title", "Укажите название расчёта"),
    "invoice": ("title", "Укажите название счёта"),
    "payment": ("title", "Укажите назначение оплаты"),
    "shipment": ("title", "Укажите название поставки"),
    "warehouse": ("name", "Укажите название склада"),
    "task": ("title", "Укажите задачу"),
    "calendar": ("title", "Укажите название события"),
    "market": ("name", "Укажите название рынка / страны"),
    "notification": ("title", "Укажите текст уведомления"),
    "carrier": ("name", "Укажите название перевозчика"),
    "vehicle": ("name", "Укажите госномер автомобиля"),
    "trailer": ("name", "Укажите номер прицепа"),
    "driver": ("full_name", "Укажите ФИО водителя"),
    "trip": ("title", "Укажите номер или название рейса"),
    "market_price": ("price", "Укажите цену"),
    "storage_unit": ("name", "Укажите название секции / силоса"),
    "inventory_lot": ("commodity", "Укажите культуру партии"),
    "warehouse_operation": ("title", "Укажите складскую операцию"),
    "availability": ("quantity", "Укажите объём предложения"),
    "demand": ("quantity", "Укажите объём спроса"),
    "alert_rule": ("target_price", "Укажите целевую цену сигнала"),
    "delivery_leg": ("quantity", "Укажите объём частичной поставки"),
    "communication": ("title", "Укажите тему коммуникации"),
    "note": ("title", "Укажите текст заметки"),
    "bank_account": ("iban", "Укажите IBAN или номер счёта"),
    "agro_operation": ("title", "Укажите культуру или название операции"),
    "weighing": ("gross", "Укажите брутто"),
    "quality_test": ("title", "Укажите анализ качества"),
    "stock_movement": ("quantity", "Укажите количество движения"),
    "expense": ("title", "Укажите расход"),
    "ops_exception": ("title", "Укажите исключение"),
    "truck_run": ("title", "Укажите рейс"),
    "agro_field": ("name", "Укажите название поля"),
    "crop_season": ("crop", "Укажите культуру сезона"),
    "field_work": ("title", "Укажите работу"),
    "machine": ("title", "Укажите машину"),
    "implement": ("title", "Укажите агрегат"),
    "material": ("name", "Укажите материал"),
    "material_movement": ("quantity", "Укажите количество"),
    "maintenance": ("title", "Укажите ТО"),
    "harvest_plan": ("title", "Укажите план уборки"),
    "harvest_actual": ("title", "Укажите факт уборки"),
    "field_cost": ("title", "Укажите расход поля"),
    "field_issue": ("title", "Укажите проблему"),
    "agro_crop": ("name", "Укажите название культуры"),
}

AUDIT_SAFE_FIELDS = (
    "name", "title", "status", "counterparty_id", "deal_id", "contract_id",
    "amount", "currency", "quantity", "price", "due_at", "planned_at",
    "type", "types", "risk_status", "risk_level", "paid_at",
    "credit_limit", "iban", "bank", "mfo", "responsible", "edrpou",
    "gross", "tare", "net", "accepted_price", "price_adjustment", "movement_type",
    "lot_id", "operation_id", "decision", "result", "quantity", "number",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _org(organization_id: str | None, tenant_id: str | None = None) -> str:
    return (organization_id or tenant_id or "default").strip() or "default"


def is_archived(row: dict[str, Any]) -> bool:
    return bool(row.get("archived_at"))


def active_only(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if not is_archived(r)]


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class AgroOpsService(
    AgroOpsProviderMixin,
    AgroOpsDeskMixin,
    AgroOpsLogisticsMixin,
    AgroOpsMarketsMixin,
    AgroOpsWarehouseMixin,
    AgroOpsFinanceMixin,
    AgroOpsAnalyticsMixin,
    AgroOpsAnalystMixin,
    AgroOpsIntelMixin,
    AgroOpsWeatherMixin,
    AgroOpsDeskSettingsMixin,
    AgroOpsCommandCenterMixin,
    AgroOpsCrmMixin,
    AgroOpsLifecycleMixin,
    AgroOpsProduction26Mixin,
    AgroOpsProductionMixin,
):
    """Org-scoped agribusiness desk with Postgres persistence + memory fallback."""

    def __init__(self) -> None:
        self._mem: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self._hydrated: set[str] = set()

    # ------------------------------------------------------------------
    # storage
    # ------------------------------------------------------------------

    def _bag(self, org: str) -> dict[str, list[dict[str, Any]]]:
        if org not in self._mem:
            self._mem[org] = {k: [] for k in KINDS}
        bag = self._mem[org]
        for k in KINDS:
            bag.setdefault(k, [])
        return bag

    async def ensure_hydrated(self, organization_id: str) -> None:
        org = _org(organization_id)
        if org in self._hydrated:
            return
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AgroOpsRepository(session)
                bag = self._bag(org)
                for kind in KINDS:
                    rows = await repo.list_kind(org, kind)
                    bag[kind] = [record_to_dict(r) for r in rows]
        except Exception as exc:
            logger.warning("agro_ops hydrate skipped: %s", exc)
        self._hydrated.add(org)

    async def _persist(self, kind: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AgroOpsRepository(session)
                row = await repo.insert(kind, data)
                return record_to_dict(row)
        except Exception as exc:
            logger.warning("agro_ops persist %s failed (memory kept): %s", kind, exc)
            return data

    async def _persist_patch(self, org: str, item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AgroOpsRepository(session)
                row = await repo.get(org, item_id)
                if row:
                    await repo.update(row, patch)
                    return record_to_dict(row)
        except Exception as exc:
            logger.warning("agro_ops patch persist skipped: %s", exc)
        return None

    async def _persist_archive(self, org: str, item_id: str, *, by: str | None, reason: str | None, restore: bool = False) -> None:
        try:
            from database.session import get_session

            async with get_session() as session:
                repo = AgroOpsRepository(session)
                row = await repo.get(org, item_id)
                if row:
                    if restore:
                        await repo.restore(row)
                    else:
                        await repo.archive(row, by=by, reason=reason)
        except Exception as exc:
            logger.warning("agro_ops archive persist skipped: %s", exc)

    # ------------------------------------------------------------------
    # audit
    # ------------------------------------------------------------------

    async def _activity(
        self,
        *,
        organization_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        summary: str,
        role: str | None = None,
        actor_id: str | None = None,
        source: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        org = _org(organization_id)

        def safe(d: dict[str, Any] | None) -> dict[str, Any] | None:
            if not d:
                return None
            return {k: d.get(k) for k in AUDIT_SAFE_FIELDS if k in d}

        item = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor_role": normalize_role(role),
            "actor_id": actor_id,
            "source": source or (payload or {}).get("source") or "user",
            "summary": summary,
            "before": safe(before),
            "after": safe(after),
            "payload": payload or {},
            "created_at": _now(),
        }
        saved = await self._persist("activity", item)
        self._bag(org)["activity"].insert(0, saved)
        return saved

    # ------------------------------------------------------------------
    # catalogs / roles
    # ------------------------------------------------------------------

    def roles(self) -> list[dict[str, Any]]:
        return roles_catalog()

    def catalogs(self) -> dict[str, Any]:
        from services.agro_ops.files import DOCUMENT_TYPES

        from services.agro_ops.logistics import CARRIER_STATUSES, CARRIER_TYPES, TRIP_STATUSES, VEHICLE_STATUSES
        from services.agro_ops.markets import MARKET_TYPES, PRICE_SOURCE_TYPES
        from services.agro_ops.warehouses import OPERATION_TYPES, WAREHOUSE_TYPES
        from services.agro_ops.command_center import DEAL_PIPELINE, SHIPMENT_STAGES
        from services.agro_ops.crm import (
            COMM_TYPES,
            CONTACT_ROLES,
            CONTRACT_STATUSES,
            CONTRACT_TYPES,
            DEAL_WORKFLOW,
            PAYMENT_SCHEDULES,
        )
        from services.agro_ops.production import (
            COST_CATEGORIES,
            FIELD_STATUSES,
            ISSUE_TYPES,
            MATERIAL_CATEGORIES,
            MATERIAL_MOVES,
            WORK_TYPES,
        )
        from services.agro_ops.production_26 import (
            MACHINE_STATUSES,
            MACHINE_TYPES,
            OWNERSHIP_TYPES,
            SOWING_STATUSES,
            WORK26_TYPES,
        )
        from services.agro_ops.operations import (
            EXCEPTION_STATUSES,
            EXPENSE_CATEGORIES,
            LOSS_KINDS,
            MOVEMENT_TYPES,
            OPERATION_STATUSES,
            QUALITY_DECISIONS,
            QUALITY_METRICS,
            QUALITY_PROFILES,
            TRANSPORT_MODES,
            TRUCK_STATUSES,
        )

        return {
            "ok": True,
            "counterparty_types": [{"id": i, "label_ru": l} for i, l in COUNTERPARTY_TYPES],
            "counterparty_statuses": [{"id": i, "label_ru": l} for i, l in COUNTERPARTY_STATUSES],
            "deal_statuses": [{"id": i, "label_ru": l} for i, l in DEAL_STATUSES],
            "document_types": [{"id": i, "label_ru": l} for i, l in DOCUMENT_TYPES],
            "default_crops": DEFAULT_CROPS,
            "currencies": DEFAULT_CURRENCIES,
            "units": DEFAULT_UNITS,
            "carrier_types": [{"id": i, "label_ru": l} for i, l in CARRIER_TYPES],
            "carrier_statuses": [{"id": i, "label_ru": l} for i, l in CARRIER_STATUSES],
            "vehicle_statuses": [{"id": i, "label_ru": l} for i, l in VEHICLE_STATUSES],
            "trip_statuses": [{"id": i, "label_ru": l} for i, l in TRIP_STATUSES],
            "market_types": [{"id": i, "label_ru": l} for i, l in MARKET_TYPES],
            "price_source_types": [{"id": i, "label_ru": l} for i, l in PRICE_SOURCE_TYPES],
            "warehouse_types": [{"id": i, "label_ru": l} for i, l in WAREHOUSE_TYPES],
            "warehouse_operations": [{"id": i, "label_ru": l} for i, l in OPERATION_TYPES],
            "deal_pipeline": [{"id": i, "label_ru": l} for i, l, _ in DEAL_PIPELINE],
            "shipment_stages": [{"id": i, "label_ru": l} for i, l, _ in SHIPMENT_STAGES],
            "contract_types": [{"id": i, "label_ru": l} for i, l in CONTRACT_TYPES],
            "contract_statuses": [{"id": i, "label_ru": l} for i, l in CONTRACT_STATUSES],
            "deal_workflow": [{"id": i, "label_ru": l} for i, l in DEAL_WORKFLOW],
            "comm_types": [{"id": i, "label_ru": l} for i, l in COMM_TYPES],
            "contact_roles": [{"id": i, "label_ru": l} for i, l in CONTACT_ROLES],
            "payment_schedules": [{"id": i, "label_ru": l} for i, l in PAYMENT_SCHEDULES.items()],
            "operation_statuses": [{"id": i, "label_ru": l} for i, l in OPERATION_STATUSES],
            "truck_statuses": [{"id": i, "label_ru": l} for i, l in TRUCK_STATUSES],
            "expense_categories": [{"id": i, "label_ru": l} for i, l in EXPENSE_CATEGORIES],
            "quality_decisions": [{"id": i, "label_ru": l} for i, l in QUALITY_DECISIONS],
            "quality_metrics": [{"id": k, **v} for k, v in QUALITY_METRICS.items()],
            "quality_profiles": QUALITY_PROFILES,
            "transport_modes": [{"id": i, "label_ru": l} for i, l in TRANSPORT_MODES],
            "movement_types": list(MOVEMENT_TYPES),
            "loss_kinds": [{"id": i, "label_ru": l} for i, l in LOSS_KINDS],
            "exception_statuses": list(EXCEPTION_STATUSES),
            "ops_version": "AGRO_2_2",
            "production_version": PROD26_VERSION,
            "field_statuses": [{"id": i, "label_ru": l} for i, l in FIELD_STATUSES],
            "work_types": [{"id": i, "label_ru": l} for i, l in WORK26_TYPES],
            "work_types_legacy": [{"id": i, "label_ru": l} for i, l in WORK_TYPES],
            "material_categories": [{"id": i, "label_ru": l} for i, l in MATERIAL_CATEGORIES],
            "material_moves": list(MATERIAL_MOVES),
            "cost_categories": [{"id": i, "label_ru": l} for i, l in COST_CATEGORIES],
            "issue_types": [{"id": i, "label_ru": l} for i, l in ISSUE_TYPES],
            "map_layers": ["crop", "status", "work", "weather", "yield", "cost"],
            "ownership_types": [{"id": i, "label_ru": l} for i, l in OWNERSHIP_TYPES],
            "sowing_statuses": [{"id": i, "label_ru": l} for i, l in SOWING_STATUSES],
            "machine_types": [{"id": i, "label_ru": l} for i, l in MACHINE_TYPES],
            "machine_statuses": [{"id": i, "label_ru": l} for i, l in MACHINE_STATUSES],
        }

    # ------------------------------------------------------------------
    # RBAC helpers per kind
    # ------------------------------------------------------------------

    def _mutation_action(self, kind: str) -> str:
        if kind in FINANCE_KINDS:
            return "finance"
        if kind in {"file", "document"}:
            return "attach"
        if kind in {"task", "calendar", "notification", "communication", "note"}:
            return "tasks"
        if kind == "intel_source":
            return "intel_admin"
        if kind in SYSTEM_KINDS:
            return "intel"
        if kind == "settings":
            return "admin"
        return "create"

    # ------------------------------------------------------------------
    # generic CRUD
    # ------------------------------------------------------------------

    async def list_entities(
        self, organization_id: str, kind: str, role: str | None = None, query: dict[str, str] | None = None
    ) -> dict[str, Any]:
        if kind not in KINDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип объекта"}
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        items = active_only(self._bag(org)[kind])
        if query:
            q = (query.get("q") or "").strip().lower()
            if q:
                items = [
                    i for i in items
                    if q in str(i.get("name") or "").lower()
                    or q in str(i.get("title") or "").lower()
                    or q in str(i.get("email") or "").lower()
                    or q in str(i.get("phone") or "").lower()
                ]
            for key in (
                "status", "type", "counterparty_id", "deal_id", "contract_id", "risk_status", "entity_id",
                "warehouse_id", "carrier_id", "vehicle_id", "market_id", "crop", "commodity",
                "source_type", "trip_id", "lot_id", "driver_id",
            ):
                val = (query.get(key) or "").strip()
                if val:
                    items = [
                        i for i in items
                        if str(i.get(key) or "") == val
                        or (key == "type" and val in (i.get("types") or []))
                    ]
        if kind == "file":
            items = self._visible_files(items, role)
        return {"ok": True, "items": items}

    SENSITIVE_DOC_TYPES = {"passport", "driver_license", "id_document", "medical"}

    def _can_see_sensitive(self, role: str | None) -> bool:
        r = normalize_role(role)
        return r in {"agro_director", "platform_owner"}

    def _visible_files(self, files: list[dict[str, Any]], role: str | None) -> list[dict[str, Any]]:
        if self._can_see_sensitive(role):
            return files
        return [f for f in files if str(f.get("doc_type") or "") not in self.SENSITIVE_DOC_TYPES]

    async def create_entity(
        self, organization_id: str, kind: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        if kind not in KINDS or kind in {"activity", "file", "report"}:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип объекта"}
        denied = require(role, self._mutation_action(kind))
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)

        if kind in {"vehicle", "trailer"}:
            body.setdefault("name", body.get("plate"))
            body.setdefault("plate", body.get("name"))
        if kind == "driver":
            body.setdefault("name", body.get("full_name"))
        if kind == "trip":
            body.setdefault("title", body.get("trip_number") or body.get("name"))
        if kind == "market_price":
            body.setdefault("price", body.get("amount"))
        req = REQUIRED_FIELD.get(kind)
        if req:
            field, msg = req
            if not str(body.get(field) or "").strip():
                return {"ok": False, "error": "validation", "message_ru": msg}

        if kind == "counterparty" and not body.get("force"):
            dups = self.find_duplicates(
                org,
                name=str(body.get("name") or ""),
                edrpou=str(body.get("edrpou") or ""),
                phone=str(body.get("phone") or ""),
                email=str(body.get("email") or ""),
                tax_id=str(body.get("tax_id") or body.get("inn") or ""),
            )
            if dups:
                return {
                    "ok": False,
                    "error": "duplicate",
                    "message_ru": "Возможно, этот контрагент уже существует",
                    "matches": dups,
                }

        item: dict[str, Any] = {k: v for k, v in body.items() if k not in {"id", "organization_id", "tenant_id", "role", "force"}}
        item.update(
            {
                "id": str(uuid.uuid4()),
                "organization_id": org,
                "tenant_id": org,
                "created_at": _now(),
                "created_by": body.get("actor_id") or normalize_role(role),
            }
        )
        item.setdefault("status", self._default_status(kind))
        # normalization per kind
        if kind == "counterparty":
            types = item.get("types") or ([item["type"]] if item.get("type") else ["counterparty"])
            if isinstance(types, str):
                types = [t.strip() for t in types.split(",") if t.strip()]
            item["types"] = types
            item.setdefault("risk_status", "normal")
            item.setdefault("risk_level", item.get("risk_level") or "LOW")
            item.setdefault("preferred_currency", "UAH")
            tags = item.get("tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            item["tags"] = tags
            if str(item.get("status") or "") in {"risk", "problem", "blocked", "blacklist"}:
                item.setdefault("status_reason", body.get("status_reason") or body.get("reason") or "")
        if kind == "contact":
            if not item.get("counterparty_id"):
                return {"ok": False, "error": "validation", "message_ru": "Контакт должен быть привязан к контрагенту"}
        if kind == "bank_account":
            if not item.get("counterparty_id"):
                return {"ok": False, "error": "validation", "message_ru": "Счёт должен быть привязан к контрагенту"}
            item.setdefault("iban", item.get("iban") or item.get("account_number"))
        credit_warning = None
        if kind == "deal":
            item.setdefault("side", body.get("side") or "buy")
            item.setdefault("currency", body.get("currency") or "UAH")
            item.setdefault("unit", body.get("unit") or "т")
            item.setdefault("title", body.get("title") or body.get("crop") or "Сделка")
            crm_meta = self.normalize_deal_crm(item, org, role)
            credit_warning = crm_meta.get("warning")
        if kind == "payment":
            item.setdefault("direction", body.get("direction") or body.get("type") or "in")
            item.setdefault("currency", body.get("currency") or "UAH")
            item["amount"] = _num(item.get("amount"))
        if kind == "crop":
            attrs = item.get("quality_attributes") or {}
            if isinstance(attrs, list):
                attrs = {str(a): None for a in attrs}
            item["quality_attributes"] = attrs
        if kind == "calendar":
            if item.get("remind_before_days") not in (None, ""):
                try:
                    item["remind_before_days"] = int(item["remind_before_days"])
                except (TypeError, ValueError):
                    item["remind_before_days"] = 1
            dedupe = f"{item.get('title')}|{item.get('starts_at')}|{item.get('deal_id') or ''}"
            existing = next((e for e in self._bag(org)["calendar"] if e.get("dedupe_key") == dedupe), None)
            if existing:
                return {"ok": False, "error": "duplicate", "message_ru": "Событие уже существует (защита от дублей)", "item": existing}
            item["dedupe_key"] = dedupe
        if kind == "calculation":
            item = self.compute_calculation(item)
        if kind in {"invoice", "payment"}:
            item["amount"] = _num(item.get("amount"))
            item.setdefault("currency", "UAH")
        if kind in {"carrier", "vehicle", "trailer", "driver", "trip"}:
            item = self.normalize_logistics_item(kind, item)
        if kind in {"market", "market_price"}:
            item = self.normalize_market_item(kind, item)
        if kind in {"warehouse", "storage_unit", "inventory_lot"}:
            item = self.normalize_warehouse_item(kind, item)
        if kind in {"availability", "demand", "alert_rule", "shipment", "task", "delivery_leg"}:
            item = self.normalize_desk_item(kind, item)

        saved = await self._persist(kind, item)
        self._bag(org)[kind].insert(0, saved)
        await self._activity(
            organization_id=org,
            entity_type=kind,
            entity_id=saved["id"],
            action=f"{kind}_created",
            summary=f"Создано: {saved.get('name') or saved.get('title')}",
            role=role,
            actor_id=body.get("actor_id"),
            after=saved,
        )
        await self._maybe_notify_on_create(org, kind, saved, role)
        await self._after_entity_create(org, kind, saved, role)
        out: dict[str, Any] = {"ok": True, "item": saved}
        if kind == "deal" and credit_warning:
            out["warning"] = credit_warning
        return out

    def _default_status(self, kind: str) -> str:
        return {
            "counterparty": "active",
            "deal": "draft",
            "contract": "draft",
            "document": "uploaded",
            "invoice": "expected",
            "payment": "planned",
            "shipment": "planned",
            "availability": "active",
            "demand": "active",
            "alert_rule": "active",
            "alert": "new",
            "delivery_leg": "recorded",
            "task": "new",
            "calendar": "scheduled",
            "market": "active",
            "notification": "new",
            "carrier": "active",
            "vehicle": "free",
            "trailer": "free",
            "driver": "active",
            "trip": "planned",
            "warehouse": "active",
            "agro_operation": "draft",
            "truck_run": "assigned",
            "ops_exception": "OPEN",
            "expense": "posted",
        }.get(kind, "active")

    async def get_entity(self, organization_id: str, kind: str, item_id: str, role: str | None = None) -> dict[str, Any]:
        if kind not in KINDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип объекта"}
        denied = require(role, "get")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = next((x for x in self._bag(org)[kind] if str(x.get("id")) == str(item_id)), None)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        files = self._visible_files(
            [
                f for f in self._bag(org)["file"]
                if str(f.get("entity_id")) == str(item_id) and not is_archived(f)
            ],
            role,
        )
        activity = [a for a in self._bag(org)["activity"] if str(a.get("entity_id")) == str(item_id)]
        return {"ok": True, "item": item, "files": files, "activity": activity}

    async def update_entity(
        self, organization_id: str, kind: str, item_id: str, body: dict[str, Any], role: str | None = None
    ) -> dict[str, Any]:
        if kind not in KINDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип объекта"}
        action = self._mutation_action(kind)
        if action == "create":
            action = "update"
        # deal approval is a director-only transition
        if kind == "deal" and str(body.get("status") or "") == "approved":
            denied = require(role, "approve")
            if denied:
                return denied
        denied = require(role, action)
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)[kind]
        idx = next((i for i, x in enumerate(bag) if str(x.get("id")) == str(item_id)), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        before = dict(bag[idx])
        cur = dict(bag[idx])
        patch = {k: v for k, v in body.items() if k not in {"id", "organization_id", "tenant_id", "role", "actor_id", "created_at"}}
        if not patch:
            return {"ok": False, "error": "validation", "message_ru": "Нет полей для обновления"}
        if kind == "deal" and "status" in patch:
            from services.agro_ops.crm import DEAL_TRANSITIONS, DEAL_WORKFLOW

            current = str(before.get("status") or "draft")
            nxt = str(patch.get("status") or "")
            if nxt and nxt != current:
                allowed = DEAL_TRANSITIONS.get(current, set())
                if nxt not in allowed:
                    return {
                        "ok": False,
                        "error": "validation",
                        "message_ru": (
                            f"Нельзя перейти из «{dict(DEAL_WORKFLOW).get(current, current)}» "
                            f"в «{dict(DEAL_WORKFLOW).get(nxt, nxt)}»"
                        ),
                        "allowed": sorted(allowed),
                    }
        if kind == "deal" and "checklist" in patch:
            for row in patch.get("checklist") or []:
                if not isinstance(row, dict):
                    continue
                if str(row.get("status")) == "received" and not row.get("file_id") and not row.get("manual_confirmed"):
                    return {
                        "ok": False,
                        "error": "validation",
                        "message_ru": "Нельзя отметить документ полученным без файла или ручного подтверждения",
                    }
        cur.update(patch)
        cur["updated_at"] = _now()
        if kind == "trip":
            from services.agro_ops.logistics import compute_trip_economics

            cur = compute_trip_economics(cur)
        if kind == "calculation":
            cur = self.compute_calculation(cur)
        persisted = await self._persist_patch(org, item_id, {**patch, **({"totals": cur.get("totals")} if kind == "calculation" else {})})
        if persisted:
            cur = persisted
        bag[idx] = cur
        act = "payment_changed" if kind == "payment" else ("approved" if str(body.get("status")) == "approved" else "edited")
        await self._activity(
            organization_id=org,
            entity_type=kind,
            entity_id=item_id,
            action=act,
            summary=f"Изменено: {cur.get('name') or cur.get('title')}",
            role=role,
            actor_id=body.get("actor_id"),
            before=before,
            after=cur,
        )
        return {"ok": True, "item": cur}

    async def archive_entity(
        self, organization_id: str, kind: str, item_id: str, body: dict[str, Any] | None = None, role: str | None = None
    ) -> dict[str, Any]:
        if kind not in KINDS:
            return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип объекта"}
        # deleting counterparties requires the delete permission (accountant cannot)
        need = "delete" if kind == "counterparty" else (self._mutation_action(kind) if kind in FINANCE_KINDS else "archive")
        if need == "finance":
            need = "finance"
        denied = require(role, need)
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)[kind]
        idx = next((i for i, x in enumerate(bag) if str(x.get("id")) == str(item_id)), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        cur = dict(bag[idx])
        cur["archived_at"] = _now()
        cur["archived_by"] = normalize_role(role)
        cur["archive_reason"] = (body or {}).get("reason") or "user"
        bag[idx] = cur
        await self._persist_archive(org, item_id, by=normalize_role(role), reason=cur["archive_reason"])
        await self._activity(
            organization_id=org,
            entity_type=kind,
            entity_id=item_id,
            action="archived",
            summary=f"В архив: {cur.get('name') or cur.get('title')}",
            role=role,
        )
        return {"ok": True, "item": cur}

    async def restore_entity(self, organization_id: str, kind: str, item_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "archive" if kind != "counterparty" else "delete")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org).get(kind, [])
        idx = next((i for i, x in enumerate(bag) if str(x.get("id")) == str(item_id)), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}
        cur = dict(bag[idx])
        for key in ("archived_at", "archived_by", "archive_reason"):
            cur.pop(key, None)
        bag[idx] = cur
        await self._persist_archive(org, item_id, by=None, reason=None, restore=True)
        await self._activity(
            organization_id=org, entity_type=kind, entity_id=item_id, action="restored",
            summary=f"Восстановлено: {cur.get('name') or cur.get('title')}", role=role,
        )
        return {"ok": True, "item": cur}

    # ------------------------------------------------------------------
    # dossier / related bundle
    # ------------------------------------------------------------------

    RELATED_KINDS = (
        "counterparty", "deal", "contract", "shipment", "warehouse", "task", "document",
        "invoice", "calculation", "payment", "carrier", "vehicle", "trailer", "driver", "trip",
        "market", "inventory_lot", "availability", "demand", "alert", "warehouse_operation",
        "agro_operation", "weighing", "quality_test", "truck_run", "expense", "ops_exception", "stock_movement",
        "agro_field", "crop_season", "field_work", "machine", "material",
    )

    async def related_bundle(self, organization_id: str, kind: str, item_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        if kind not in self.RELATED_KINDS:
            return {"ok": False, "error": "validation", "message_ru": "Связки доступны для основных объектов АГРО"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)
        base = next((x for x in bag[kind] if str(x.get("id")) == str(item_id)), None)
        if not base:
            return {"ok": False, "error": "not_found", "message_ru": "Объект не найден"}

        cp_ids: set[str] = set()
        deal_ids: set[str] = set()
        if kind == "counterparty":
            cp_ids.add(str(item_id))
        elif kind == "deal":
            deal_ids.add(str(item_id))
            if base.get("counterparty_id"):
                cp_ids.add(str(base["counterparty_id"]))
        else:
            if base.get("deal_id"):
                deal_ids.add(str(base["deal_id"]))
            if base.get("counterparty_id"):
                cp_ids.add(str(base["counterparty_id"]))

        def anchored(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return active_only(
                [
                    r for r in rows
                    if str(r.get("deal_id") or "") in deal_ids
                    or str(r.get("counterparty_id") or "") in cp_ids
                ]
            )

        deals = (
            anchored(bag["deal"])
            if kind == "counterparty"
            else active_only([d for d in bag["deal"] if str(d.get("id")) in deal_ids])
        )
        if kind == "counterparty":
            deal_ids |= {str(d["id"]) for d in deals}
        counterparties = active_only([c for c in bag["counterparty"] if str(c.get("id")) in cp_ids])

        related = {
            "counterparties": counterparties,
            "contacts": active_only([c for c in bag["contact"] if str(c.get("counterparty_id") or "") in cp_ids]),
            "deals": deals,
            "contracts": anchored(bag["contract"]),
            "documents": anchored(bag["document"]),
            "calculations": anchored(bag["calculation"]),
            "invoices": anchored(bag["invoice"]),
            "payments": anchored(bag["payment"]),
            "shipments": anchored(bag["shipment"]),
            "tasks": anchored(bag["task"]),
            "calendar": anchored(bag["calendar"]),
            "files": self._visible_files(active_only([f for f in bag["file"] if str(f.get("entity_id")) == str(item_id)]), role),
            "activity": [a for a in bag["activity"] if str(a.get("entity_id")) == str(item_id)],
            "communications": anchored(bag.get("communication") or []),
            "notes": anchored(bag.get("note") or []),
            "bank_accounts": active_only([b for b in bag.get("bank_account") or [] if str(b.get("counterparty_id") or "") in cp_ids]),
            "trips": active_only(
                [t for t in bag.get("trip") or [] if str(t.get("deal_id") or "") in deal_ids or str(t.get("counterparty_id") or "") in cp_ids or str(t.get("shipment_id") or "") == str(item_id)]
            ),
            "vehicles": active_only([v for v in bag.get("vehicle") or [] if str(v.get("carrier_id") or "") == str(item_id) or str(v.get("counterparty_id") or "") in cp_ids]),
            "lots": active_only([x for x in bag.get("inventory_lot") or [] if str(x.get("warehouse_id") or "") == str(item_id) or str(x.get("deal_id") or "") in deal_ids]),
            "warehouse_operations": active_only(
                [
                    o for o in bag.get("warehouse_operation") or []
                    if str(o.get("warehouse_id") or "") == str(item_id)
                    or str(o.get("deal_id") or "") in deal_ids
                    or str(o.get("shipment_id") or "") == str(item_id)
                    or str(o.get("counterparty_id") or "") in cp_ids
                ]
            ),
            "notes": (
                [{"id": f"note-{item_id}", "title": str(base.get("notes") or "").strip(), "status": "note"}]
                if str(base.get("notes") or "").strip()
                else []
            ),
        }
        if kind == "deal" and can(role, "margins"):
            calcs = related.get("calculations") or []
            latest_calc = calcs[0] if calcs else None
            related["margin"] = (latest_calc or {}).get("totals") if latest_calc else None
        elif kind == "deal":
            related["margin"] = None
        # exclude self from own list
        key_self = {"counterparty": "counterparties", "deal": "deals", "contract": "contracts",
                    "document": "documents", "task": "tasks", "shipment": "shipments",
                    "invoice": "invoices", "calculation": "calculations"}.get(kind)
        if key_self:
            related[key_self] = [r for r in related[key_self] if str(r.get("id")) != str(item_id)]
        return {"ok": True, "item": base, "related": related}

    # ------------------------------------------------------------------
    # files
    # ------------------------------------------------------------------

    async def upload_file(
        self,
        organization_id: str,
        *,
        filename: str,
        mime_type: str | None,
        data: bytes,
        entity_type: str | None,
        entity_id: str | None,
        doc_type: str | None = None,
        title: str | None = None,
        issue_date: str | None = None,
        expiry_date: str | None = None,
        comments: str | None = None,
        tags: list[str] | str | None = None,
        role: str | None = None,
        actor_id: str | None = None,
    ) -> dict[str, Any]:
        from services.agro_ops import files as fstore
        from services.agro_ops.files import ATTACHABLE_ENTITY_TYPES

        denied = require(role, "attach")
        if denied:
            return denied
        bad = fstore.validate_upload(filename, mime_type)
        if bad:
            return bad
        if entity_type and entity_type not in ATTACHABLE_ENTITY_TYPES:
            return {"ok": False, "error": "validation", "message_ru": "Недопустимый тип объекта для вложения"}
        if not data:
            return {"ok": False, "error": "validation", "message_ru": "Пустой файл"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        file_id = str(uuid.uuid4())
        storage_path = fstore.write_bytes(org, file_id, data)
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        item = {
            "id": file_id,
            "organization_id": org,
            "tenant_id": org,
            "filename": filename,
            "title": title or filename,
            "mime_type": mime_type,
            "size_bytes": len(data),
            "doc_type": doc_type or "other",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "storage_path": storage_path,
            "uploaded_by": actor_id or normalize_role(role),
            "issue_date": issue_date,
            "expiry_date": expiry_date,
            "comments": comments,
            "tags": tags or [],
            "status": "active",
            "created_at": _now(),
        }
        saved = await self._persist("file", item)
        saved.setdefault("storage_path", storage_path)
        self._bag(org)["file"].insert(0, saved)
        await self._activity(
            organization_id=org, entity_type=entity_type or "file", entity_id=str(entity_id or file_id),
            action="document_attached", summary=f"Файл прикреплён: {filename}", role=role, actor_id=actor_id,
        )
        return {"ok": True, "item": saved}

    async def get_file(self, organization_id: str, file_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "get")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        item = next((f for f in self._bag(org)["file"] if str(f.get("id")) == str(file_id)), None)
        if not item:
            return {"ok": False, "error": "not_found", "message_ru": "Файл не найден"}
        if str(item.get("doc_type") or "") in self.SENSITIVE_DOC_TYPES and not self._can_see_sensitive(role):
            return {"ok": False, "error": "forbidden", "message_ru": "Персональные документы доступны только директору"}
        return {"ok": True, "item": item}

    async def file_content(self, organization_id: str, file_id: str, role: str | None = None) -> dict[str, Any]:
        from services.agro_ops import files as fstore

        res = await self.get_file(organization_id, file_id, role)
        if not res.get("ok"):
            return res
        item = res["item"]
        data = fstore.read_bytes(str(item.get("storage_path") or ""))
        if data is None:
            return {"ok": False, "error": "not_found", "message_ru": "Содержимое файла недоступно"}
        return {"ok": True, "item": item, "data": data}

    async def rename_file(self, organization_id: str, file_id: str, new_name: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "attach")
        if denied:
            return denied
        new_name = (new_name or "").strip()
        if not new_name:
            return {"ok": False, "error": "validation", "message_ru": "Укажите новое имя файла"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)["file"]
        idx = next((i for i, f in enumerate(bag) if str(f.get("id")) == str(file_id)), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Файл не найден"}
        cur = dict(bag[idx])
        cur["filename"] = new_name
        cur["title"] = new_name
        bag[idx] = cur
        await self._persist_patch(org, file_id, {"filename": new_name, "title": new_name})
        await self._activity(
            organization_id=org, entity_type="file", entity_id=file_id, action="edited",
            summary=f"Файл переименован: {new_name}", role=role,
        )
        return {"ok": True, "item": cur}

    async def relink_file(
        self, organization_id: str, file_id: str, entity_type: str, entity_id: str, role: str | None = None
    ) -> dict[str, Any]:
        from services.agro_ops.files import ATTACHABLE_ENTITY_TYPES

        denied = require(role, "attach")
        if denied:
            return denied
        if entity_type not in ATTACHABLE_ENTITY_TYPES:
            return {"ok": False, "error": "validation", "message_ru": "Недопустимый тип объекта для вложения"}
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)["file"]
        idx = next((i for i, f in enumerate(bag) if str(f.get("id")) == str(file_id)), None)
        if idx is None:
            return {"ok": False, "error": "not_found", "message_ru": "Файл не найден"}
        cur = dict(bag[idx])
        cur["entity_type"] = entity_type
        cur["entity_id"] = entity_id
        bag[idx] = cur
        await self._persist_patch(org, file_id, {"entity_type": entity_type, "entity_id": entity_id})
        await self._activity(
            organization_id=org, entity_type="file", entity_id=file_id, action="edited",
            summary="Файл перепривязан", role=role,
        )
        return {"ok": True, "item": cur}

    # ------------------------------------------------------------------
    # notifications
    # ------------------------------------------------------------------

    async def _maybe_notify_on_create(self, org: str, kind: str, item: dict[str, Any], role: str | None) -> None:
        titles = {
            "payment": "Создана оплата",
            "shipment": "Создана поставка",
            "report": "Новый обзор Агро-разведки",
        }
        if kind not in titles:
            return
        note = {
            "id": str(uuid.uuid4()),
            "organization_id": org,
            "tenant_id": org,
            "title": f"{titles[kind]}: {item.get('title') or item.get('name')}",
            "kind": kind,
            "entity_id": item.get("id"),
            "deeplink": f"/workspace/agro?view={'accounting' if kind == 'payment' else ('shipments' if kind == 'shipment' else 'intel')}",
            "channel": "in_app",
            "status": "new",
            "created_at": _now(),
        }
        saved = await self._persist("notification", note)
        self._bag(org)["notification"].insert(0, saved)

    # ------------------------------------------------------------------
    # dashboard
    # ------------------------------------------------------------------

    async def dashboard(self, organization_id: str, role: str | None = None) -> dict[str, Any]:
        denied = require(role, "list")
        if denied:
            return denied
        org = _org(organization_id)
        await self.ensure_hydrated(org)
        bag = self._bag(org)
        cps = active_only(bag["counterparty"])
        deals = active_only(bag["deal"])
        tasks = active_only(bag["task"])
        today = datetime.now(timezone.utc).date().isoformat()

        def has_type(cp: dict[str, Any], t: str) -> bool:
            return t in (cp.get("types") or [])

        fin = self.finance_summary_data(org)
        overdue_tasks = [
            t for t in tasks
            if t.get("due_at") and str(t.get("due_at"))[:10] < today and str(t.get("status")) not in {"done", "cancelled"}
        ]
        cards = {
            "counterparties": len(cps),
            "farmers": len([c for c in cps if has_type(c, "farmer") or has_type(c, "farm")]),
            "companies": len([c for c in cps if has_type(c, "agro_company")]),
            "suppliers": len([c for c in cps if has_type(c, "supplier")]),
            "buyers": len([c for c in cps if has_type(c, "buyer")]),
            "active_contracts": len([c for c in active_only(bag["contract"]) if str(c.get("status")) not in {"closed", "cancelled"}]),
            "receivables": fin["receivables_total"],
            "payables": fin["payables_total"],
            "active_shipments": len([s for s in active_only(bag["shipment"]) if str(s.get("status")) in {"planned", "in_transit"}]),
            "tasks_today": len([t for t in tasks if str(t.get("due_at") or "")[:10] == today and str(t.get("status")) not in {"done", "cancelled"}]),
            "overdue_tasks": len(overdue_tasks),
            "active_deals": len([d for d in deals if str(d.get("status")) not in {"closed", "cancelled", "draft"}]),
            "active_trips": len([t for t in active_only(bag.get("trip") or []) if str(t.get("status")) in {"planned", "assigned", "loading", "in_transit", "unloading"}]),
            "warehouses": len(active_only(bag.get("warehouse") or [])),
            "markets": len(active_only(bag.get("market") or [])),
        }
        cc = self.build_command_center(org, role)
        grain = await self.grain_today(org, role)
        if grain.get("ok"):
            cc["grain_today"] = grain.get("metrics") or []
            cc["ops_version"] = grain.get("version") or "AGRO_2_2"
        agro_today = await self.agronomist_today(org, role)
        if agro_today.get("ok"):
            cc["agronomist_today"] = agro_today.get("metrics") or []
            cc["production_version"] = agro_today.get("version") or PROD26_VERSION
            cc["kpis_26"] = agro_today.get("kpis_26") or []
        director_prod = await self.director_production(org, role)
        if director_prod.get("ok"):
            cc["director_production"] = director_prod
            if director_prod.get("kpis_26"):
                cc["kpis_26"] = director_prod.get("kpis_26")
        stock = await self.grain_stock(org, role)
        if stock.get("ok"):
            cc["grain_stock"] = {
                "by_crop": stock.get("by_crop") or [],
                "by_warehouse": stock.get("by_warehouse") or [],
                "lots": stock.get("lots") or [],
            }
        overdue_invoices = list(fin.get("overdue") or [])
        if cc.get("grain_today"):
            for m in cc["grain_today"]:
                if m.get("id") == "pay_overdue":
                    m["value"] = len(overdue_invoices)
        return {
            "ok": True,
            "organization_id": org,
            "role": normalize_role(role),
            "cards": cards,
            "overdue_tasks": overdue_tasks[:10],
            "recent_activity": bag["activity"][:10],
            "onboarding": {
                "title_ru": "Добро пожаловать в Агро",
                "steps": [
                    "Создать контрагента",
                    "Создать сделку",
                    "Прикрепить договор",
                    "Сделать расчёт",
                    "Добавить поставку",
                    "Открыть Агро-разведку",
                ],
            },
            "command_center": cc,
            "command_center_version": "AGRO_2_0",
            "channels": self.notification_channels(),
            "demo_mode": any(s.get("demo_loaded") or s.get("production_demo_loaded") for s in active_only(bag.get("settings") or [])),
            "demo_notice_ru": (
                "РЕЖИМ DEMO. Загруженные демо-строки помечены [DEMO] и не используются в производственном анализе и обзорах."
                if any(s.get("demo_loaded") or s.get("production_demo_loaded") for s in active_only(bag.get("settings") or []))
                else None
            ),
        }

    def notification_channels(self) -> dict[str, Any]:
        import os

        telegram = bool(os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN"))
        email = bool(os.environ.get("SMTP_HOST") or os.environ.get("EMAIL_SMTP_HOST"))
        return {
            "in_app": {"id": "in_app", "connected": True, "label_ru": "В приложении", "status": "LIVE"},
            "telegram": {
                "id": "telegram",
                "connected": telegram,
                "label_ru": "Telegram" if telegram else "Telegram — не настроен",
                "status": "LIVE" if telegram else "NOT_CONFIGURED",
            },
            "email": {
                "id": "email",
                "connected": email,
                "label_ru": "Эл. почта" if email else "Эл. почта — не настроена",
                "status": "LIVE" if email else "NOT_CONFIGURED",
            },
        }


_SVC: AgroOpsService | None = None


def get_agro_ops_service() -> AgroOpsService:
    global _SVC
    if _SVC is None:
        _SVC = AgroOpsService()
    return _SVC


def reset_agro_ops_for_tests() -> None:
    global _SVC
    _SVC = None
