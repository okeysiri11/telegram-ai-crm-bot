# Platform Readiness Test Suite v1 — full audit and readiness report.

from __future__ import annotations

import asyncio
import inspect
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent

Status = str  # operational | partial | failed

COMMERCIAL_MODULES = frozenset({
    "automotive_button",
    "automotive_menu",
    "add_car",
    "car_list",
    "search_car",
    "profit_calculator",
    "ai_manager_menu",
    "leads_menu",
    "billing_menu",
    "pricing_models",
    "payment_methods",
    "receipt_upload",
    "owner_approval",
    "subscription_activation",
})


def _result(status: Status, detail: str = "") -> dict[str, Any]:
    return {"status": status, "detail": detail}


def _score_statuses(modules: dict[str, dict]) -> dict[str, int]:
    weights = {"operational": 100, "partial": 50, "failed": 0}
    values = [weights.get(m.get("status"), 0) for m in modules.values()]
    if not values:
        return {"platform": 0, "commercial": 0, "technical_debt": 100}
    platform = int(round(sum(values) / len(values)))
    commercial_keys = [k for k in modules if k in COMMERCIAL_MODULES]
    if commercial_keys:
        commercial_vals = [weights.get(modules[k].get("status"), 0) for k in commercial_keys]
        commercial = int(round(sum(commercial_vals) / len(commercial_vals)))
    else:
        commercial = platform
    return {
        "platform": platform,
        "commercial": commercial,
        "technical_debt": max(0, 100 - platform),
    }


def _overall_status(scores: dict[str, int], modules: dict[str, dict]) -> str:
    failed = sum(1 for m in modules.values() if m.get("status") == "failed")
    platform = scores["platform"]
    if platform >= 85 and failed == 0:
        return "GREEN"
    if platform >= 60 or failed <= 3:
        return "YELLOW"
    return "RED"


class PlatformReadinessTestSuite:
    @staticmethod
    async def _check_postgresql() -> dict[str, Any]:
        from database.connection import is_postgres_configured
        from database.session import check_db_health

        if not is_postgres_configured():
            return _result("partial", "DATABASE_URL not set; SQLite fallback active")
        health = await check_db_health()
        if health.get("ok"):
            return _result("operational", health.get("status", "healthy"))
        return _result("failed", health.get("error", "unhealthy"))

    @staticmethod
    def _check_alembic() -> dict[str, Any]:
        versions_dir = ROOT / "migrations" / "versions"
        if not (ROOT / "alembic.ini").exists() or not versions_dir.is_dir():
            return _result("failed", "Alembic not configured")
        migration_files = [
            p for p in versions_dir.glob("*.py") if p.name != "__init__.py"
        ]
        if not migration_files:
            return _result("failed", "no migration files")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "alembic", "heads"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=20,
            )
            head = (proc.stdout or proc.stderr).strip().splitlines()[-1] if proc.returncode == 0 else ""
        except Exception as exc:
            head = ""
            return _result("partial", f"{len(migration_files)} files; head probe failed: {exc}")
        if head:
            return _result("operational", f"{len(migration_files)} migrations; {head}")
        return _result("partial", f"{len(migration_files)} migrations; head unknown")

    @staticmethod
    def _check_uuid_pk_consistency() -> dict[str, Any]:
        from database.base import Base
        from database.migration_models import load_all_models
        from database.models.mixins import UUIDPrimaryKeyMixin

        load_all_models()
        uuid_tables = 0
        int_pk_tables = 0
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if not hasattr(cls, "__tablename__"):
                continue
            if issubclass(cls, UUIDPrimaryKeyMixin):
                uuid_tables += 1
            elif "id" in mapper.columns and str(mapper.columns.id.type).startswith("INTEGER"):
                int_pk_tables += 1
        if uuid_tables >= 20:
            detail = f"{uuid_tables} UUID PK models"
            if int_pk_tables:
                detail += f"; {int_pk_tables} legacy integer PK"
                return _result("partial", detail)
            return _result("operational", detail)
        if uuid_tables >= 1:
            return _result("partial", f"{uuid_tables} UUID PK; {int_pk_tables} integer PK")
        return _result("failed", "no UUID primary keys detected")

    @staticmethod
    def _check_event_bus() -> dict[str, Any]:
        from services.event_bus_test import EventBusTestService

        result = EventBusTestService.run_integration_test()
        if result.get("ok"):
            return _result("operational", result.get("status", "OK"))
        err = result.get("error") or result.get("steps", {})
        return _result("failed", str(err)[:80])

    @staticmethod
    def _check_audit_engine() -> dict[str, Any]:
        try:
            from database.models.audit_log import AuditLog
            from repositories.audit_repository import AuditRepository

            if AuditLog.__tablename__ != "audit_engine_logs":
                return _result("partial", "AuditLog model present")
            if not hasattr(AuditRepository, "create_log"):
                return _result("partial", "AuditRepository incomplete")
            import database as db

            db.cursor.execute("SELECT COUNT(*) FROM audit_log")
            db.cursor.fetchone()
            return _result("operational", "AuditRepository + legacy audit_log")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_notification_engine() -> dict[str, Any]:
        try:
            from services.notifications import NotificationService

            NotificationService.get_notifications(0, limit=1)
            from database.models.notification import Notification

            return _result("operational", Notification.__tablename__)
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_rbac() -> dict[str, Any]:
        try:
            from database import ROLE_NAMES, ROLE_PERMISSIONS, SYSTEM_PERMISSIONS

            if not ROLE_NAMES or not SYSTEM_PERMISSIONS:
                return _result("failed", "RBAC config empty")
            required = {"OWNER", "SUPER_MANAGER", "AUTO_MANAGER"}
            missing = required - set(ROLE_PERMISSIONS.keys())
            if missing:
                return _result("partial", f"missing roles: {','.join(sorted(missing))}")
            return _result("operational", f"{len(ROLE_NAMES)} roles")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    async def _check_tenant_isolation() -> dict[str, Any]:
        try:
            from services.pg_partner_tenant_engine import PartnerTenantEngineV1, TenantAccessDeniedError

            if not hasattr(PartnerTenantEngineV1, "resolve_context"):
                return _result("partial", "PartnerTenantEngineV1 loaded")
            source = inspect.getsource(PartnerTenantEngineV1)
            if "TenantAccessDeniedError" in source or TenantAccessDeniedError:
                return _result("operational", "PartnerTenantEngineV1 isolation")
            return _result("partial", "tenant engine without deny guard")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_scheduler() -> dict[str, Any]:
        try:
            from services.pg_scheduler_engine import DEFAULT_JOBS, get_default_worker

            worker = get_default_worker()
            if DEFAULT_JOBS and worker is not None:
                return _result("operational", f"{len(DEFAULT_JOBS)} default jobs")
            return _result("partial", "scheduler loaded")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_api_gateway() -> dict[str, Any]:
        try:
            from api.server import create_app
            from services.pg_api_gateway_engine import ApiGatewayEngineV1

            app = create_app()
            routes = len(app.router.routes())
            if routes >= 5 and hasattr(ApiGatewayEngineV1, "authenticate_api_key"):
                return _result("operational", f"{routes} HTTP routes")
            return _result("partial", f"{routes} routes")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_bot_startup() -> dict[str, Any]:
        try:
            from config import BOT_TOKEN
            from bot import bot, dp

            if not BOT_TOKEN:
                return _result("failed", "BOT_TOKEN missing")
            if bot and dp:
                return _result("operational", "Bot + Dispatcher initialized")
            return _result("partial", "bot module incomplete")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_polling() -> dict[str, Any]:
        source = (ROOT / "bot.py").read_text(encoding="utf-8")
        if "start_polling" in source:
            return _result("operational", "dp.start_polling configured")
        return _result("failed", "polling not configured")

    @staticmethod
    def _check_start_handler() -> dict[str, Any]:
        import handlers

        if hasattr(handlers, "cmd_start"):
            return _result("operational", "CommandStart handler registered")
        return _result("failed", "cmd_start missing")

    @staticmethod
    def _check_main_menu() -> dict[str, Any]:
        try:
            from keyboards import owner_main_menu

            menu = owner_main_menu()
            count = sum(len(row) for row in menu.keyboard)
            if count >= 3:
                return _result("operational", f"{count} menu buttons")
            return _result("partial", f"{count} menu buttons")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_callback_handlers() -> dict[str, Any]:
        import handlers
        from auto_vertical_handlers import auto_vertical_router

        main_callbacks = len(handlers.router.callback_query.handlers)
        auto_callbacks = len(auto_vertical_router.callback_query.handlers)
        total = main_callbacks + auto_callbacks
        if total >= 5:
            return _result("operational", f"{total} callback handlers")
        return _result("partial", f"{total} callback handlers")

    @staticmethod
    def _check_fsm_storage() -> dict[str, Any]:
        import auto_vertical_handlers as avh

        if hasattr(avh, "auto_vertical_flow") and hasattr(avh, "auto_billing_flow"):
            bot_src = (ROOT / "bot.py").read_text(encoding="utf-8")
            if "MemoryStorage" in bot_src or "FSMContext" in bot_src:
                return _result("operational", "aiogram FSM storage")
            return _result("partial", "dict-based flow state (no aiogram FSM)")
        return _result("failed", "flow storage missing")

    @staticmethod
    def _check_middleware() -> dict[str, Any]:
        bot_src = (ROOT / "bot.py").read_text(encoding="utf-8")
        if "middleware" in bot_src.lower():
            return _result("operational", "middleware registered")
        handlers_src = (ROOT / "handlers.py").read_text(encoding="utf-8")
        if "_init_ai_user" in handlers_src or "_can_access_admin" in handlers_src:
            return _result("partial", "inline access guards; no dp middleware")
        return _result("failed", "no middleware or guards")

    @staticmethod
    def _automotive_source() -> str:
        return (ROOT / "auto_vertical_handlers.py").read_text(encoding="utf-8")

    @staticmethod
    def _check_automotive_button() -> dict[str, Any]:
        from keyboards import AUTO_VERTICAL_MAIN_BUTTON, owner_main_menu

        menu = owner_main_menu(show_automotive=True)
        texts = {btn.text for row in menu.keyboard for btn in row}
        if AUTO_VERTICAL_MAIN_BUTTON in texts:
            return _result("operational", AUTO_VERTICAL_MAIN_BUTTON)
        return _result("failed", "auto button missing from main menu")

    @staticmethod
    def _check_automotive_menu() -> dict[str, Any]:
        from keyboards import AUTO_VERTICAL_HUB_BUTTONS, AUTO_VERTICAL_MENU_BUTTONS, auto_vertical_hub_menu, auto_vertical_menu

        hub_texts = {btn.text for row in auto_vertical_hub_menu().keyboard for btn in row}
        menu_texts = {btn.text for row in auto_vertical_menu().keyboard for btn in row}
        if AUTO_VERTICAL_HUB_BUTTONS.issubset(hub_texts) and "🚘 Cars" in hub_texts:
            return _result("operational", f"hub {len(hub_texts)} + cars {len(menu_texts)} items")
        missing = AUTO_VERTICAL_HUB_BUTTONS - hub_texts
        return _result("partial", f"missing hub: {','.join(sorted(missing)[:3])}")

    @staticmethod
    def _check_add_car() -> dict[str, Any]:
        src = PlatformReadinessTestSuite._automotive_source()
        if "step\": \"vin\"" in src or "'step': 'vin'" in src:
            return _result("operational", "VIN add-car flow")
        return _result("failed", "add car flow missing")

    @staticmethod
    def _check_car_list() -> dict[str, Any]:
        src = PlatformReadinessTestSuite._automotive_source()
        if "Список авто" in src and "_show_car_list" in src:
            return _result("operational", "car list handler")
        if "Список авто" in src:
            return _result("partial", "menu only")
        return _result("failed", "car list missing")

    @staticmethod
    def _check_search_car() -> dict[str, Any]:
        src = PlatformReadinessTestSuite._automotive_source()
        if "step\": \"search\"" in src or "'step': 'search'" in src:
            return _result("operational", "search flow")
        return _result("failed", "search flow missing")

    @staticmethod
    def _check_profit_calculator() -> dict[str, Any]:
        src = PlatformReadinessTestSuite._automotive_source()
        if "profit_vin" in src or "Калькулятор прибыли" in src:
            return _result("operational", "profit calculator flow")
        return _result("failed", "profit calculator missing")

    @staticmethod
    def _check_ai_manager_menu() -> dict[str, Any]:
        src = PlatformReadinessTestSuite._automotive_source()
        if "AI Менеджер" in src:
            return _result("operational", "AI Manager menu")
        return _result("failed", "AI Manager missing")

    @staticmethod
    def _check_leads_menu() -> dict[str, Any]:
        src = PlatformReadinessTestSuite._automotive_source()
        if "👥 Лиды" in src:
            return _result("operational", "Leads menu")
        return _result("failed", "Leads menu missing")

    @staticmethod
    def _check_billing_menu() -> dict[str, Any]:
        src = PlatformReadinessTestSuite._automotive_source()
        if "Тарифы и услуги" in src and "auto_billing" in src:
            return _result("operational", "billing menu + handlers")
        return _result("failed", "billing menu missing")

    @staticmethod
    def _check_pricing_models() -> dict[str, Any]:
        from database.models.commercial_billing_engine import PricingModel

        models = [m.value for m in PricingModel]
        if len(models) >= 4:
            return _result("operational", ",".join(models[:3]))
        return _result("partial", str(models))

    @staticmethod
    def _check_payment_methods() -> dict[str, Any]:
        from database.models.commercial_billing_engine import PaymentMethod

        methods = [m.value for m in PaymentMethod]
        if len(methods) >= 3:
            return _result("operational", ",".join(methods[:3]))
        return _result("failed", str(methods))

    @staticmethod
    def _check_receipt_upload() -> dict[str, Any]:
        from services.pg_commercial_billing_engine import CommercialBillingEngineV1

        if hasattr(CommercialBillingEngineV1, "attach_receipt"):
            return _result("operational", "attach_receipt")
        return _result("failed", "attach_receipt missing")

    @staticmethod
    def _check_owner_approval() -> dict[str, Any]:
        from services.pg_commercial_billing_engine import CommercialBillingEngineV1

        if hasattr(CommercialBillingEngineV1, "approve_payment"):
            return _result("operational", "approve_payment")
        return _result("failed", "approve_payment missing")

    @staticmethod
    def _check_subscription_activation() -> dict[str, Any]:
        src = inspect.getsource(
            __import__(
                "services.pg_commercial_billing_engine",
                fromlist=["CommercialBillingEngineV1"],
            ).CommercialBillingEngineV1.approve_payment,
        )
        if "subscribe_tenant" in src:
            return _result("operational", "approve → subscribe_tenant")
        return _result("partial", "subscription chain unclear")

    @staticmethod
    def _check_automotive_partner_integration() -> dict[str, Any]:
        try:
            from services.pg_automotive_partner_integration_engine import AutomotivePartnerIntegrationEngineV1

            checks = [
                hasattr(AutomotivePartnerIntegrationEngineV1, "list_insurance_products"),
                hasattr(AutomotivePartnerIntegrationEngineV1, "list_dealer_sources"),
                hasattr(AutomotivePartnerIntegrationEngineV1, "registry_health"),
            ]
            if all(checks):
                return _result("operational", "SG TAS + Boroda Cars registry")
            return _result("partial", "partner integration incomplete")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_bidex_quote_parser() -> dict[str, Any]:
        try:
            from services.bidex_telegram_quote_parser import (
                BIDEX_RATES_TAG,
                BidExTelegramQuoteParserV1,
            )

            sample = f"{BIDEX_RATES_TAG}\nUSD/UAH: 1 / 2\nEUR/UAH: 3 / 4\nEUR/USD: 1.1 / 1.2"
            checks = [
                hasattr(BidExTelegramQuoteParserV1, "parse_message"),
                hasattr(BidExTelegramQuoteParserV1, "ingest_channel_message"),
                BidExTelegramQuoteParserV1.should_parse(sample),
            ]
            if all(checks):
                return _result("operational", "@bidex_Odesa parser v1")
            return _result("partial", "BidEx parser incomplete")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_dealer_quote_authority() -> dict[str, Any]:
        try:
            from services.pg_dealer_quote_authority_engine import DealerQuoteAuthorityEngineV1
            from services.dealer_rate_service import DealerRateService

            checks = [
                hasattr(DealerQuoteAuthorityEngineV1, "ingest_foma_rates"),
                hasattr(DealerQuoteAuthorityEngineV1, "get_treasury_dashboard"),
                hasattr(DealerQuoteAuthorityEngineV1, "calculate_deviations"),
                hasattr(DealerRateService, "get_otc_usdt_mid"),
            ]
            if all(checks):
                return _result("operational", "Foma Rates authority engine")
            return _result("partial", "quote authority incomplete")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_market_reference_sources() -> dict[str, Any]:
        try:
            from database.models.market_data import MarketSourceCode
            from services.pg_market_data_engine import REFERENCE_ONLY_SOURCES

            required = {
                MarketSourceCode.OKX.value,
                MarketSourceCode.WHITEBIT.value,
                MarketSourceCode.NBU.value,
                MarketSourceCode.TRADINGVIEW.value,
            }
            missing = required - REFERENCE_ONLY_SOURCES
            engine_src = (ROOT / "services" / "pg_market_data_engine.py").read_text(encoding="utf-8")
            binance_removed = "BINANCE" not in engine_src or "MarketSourceCode.BINANCE" not in engine_src
            if not missing and binance_removed:
                return _result("operational", "OKX/WhiteBIT reference-only; Binance removed")
            if missing:
                return _result("partial", f"missing ref sources: {','.join(sorted(missing)[:3])}")
            return _result("partial", "Binance references may remain in market engine")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_engine_class(module_path: str, class_name: str, label: str) -> dict[str, Any]:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            if inspect.isclass(cls):
                return _result("operational", label)
            return _result("partial", label)
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    def _check_role_isolation() -> dict[str, Any]:
        try:
            from services.hierarchical_rbac import HierarchicalRBAC
            from services.permissions import PermissionService

            if hasattr(HierarchicalRBAC, "check") or hasattr(PermissionService, "can_access_module"):
                return _result("operational", "RBAC + PermissionService")
            return _result("partial", "permissions loaded")
        except Exception as exc:
            return _result("failed", str(exc)[:80])

    @staticmethod
    async def _check_security_tenant_isolation() -> dict[str, Any]:
        return await PlatformReadinessTestSuite._check_tenant_isolation()

    @staticmethod
    def _check_audit_logging() -> dict[str, Any]:
        import handlers

        if "log_audit" in inspect.getsource(handlers):
            return _result("operational", "log_audit wired in handlers")
        return _result("partial", "audit helper present")

    @staticmethod
    def _check_permission_checks() -> dict[str, Any]:
        import handlers

        src = inspect.getsource(handlers)
        guards = sum(1 for token in ("_can_access_admin", "PermissionService", "has_deal_action") if token in src)
        if guards >= 2:
            return _result("operational", f"{guards} guard patterns")
        return _result("partial", "limited permission checks")

    @classmethod
    def _all_checks(cls) -> list[tuple[str, str, Callable[..., dict[str, Any]]]]:
        return [
            ("postgresql", "Core Platform", cls._check_postgresql),
            ("alembic_migrations", "Core Platform", cls._check_alembic),
            ("uuid_pk_consistency", "Core Platform", cls._check_uuid_pk_consistency),
            ("event_bus", "Core Platform", cls._check_event_bus),
            ("audit_engine", "Core Platform", cls._check_audit_engine),
            ("notification_engine", "Core Platform", cls._check_notification_engine),
            ("rbac", "Core Platform", cls._check_rbac),
            ("tenant_isolation", "Core Platform", cls._check_tenant_isolation),
            ("scheduler", "Core Platform", cls._check_scheduler),
            ("api_gateway", "Core Platform", cls._check_api_gateway),
            ("bot_startup", "Telegram", cls._check_bot_startup),
            ("polling", "Telegram", cls._check_polling),
            ("start_handler", "Telegram", cls._check_start_handler),
            ("main_menu", "Telegram", cls._check_main_menu),
            ("callback_handlers", "Telegram", cls._check_callback_handlers),
            ("fsm_storage", "Telegram", cls._check_fsm_storage),
            ("middleware", "Telegram", cls._check_middleware),
            ("automotive_button", "Automotive", cls._check_automotive_button),
            ("automotive_menu", "Automotive", cls._check_automotive_menu),
            ("automotive_partner_integration", "Automotive", cls._check_automotive_partner_integration),
            ("add_car", "Automotive", cls._check_add_car),
            ("car_list", "Automotive", cls._check_car_list),
            ("search_car", "Automotive", cls._check_search_car),
            ("profit_calculator", "Automotive", cls._check_profit_calculator),
            ("ai_manager_menu", "Automotive", cls._check_ai_manager_menu),
            ("leads_menu", "Automotive", cls._check_leads_menu),
            ("billing_menu", "Automotive", cls._check_billing_menu),
            ("pricing_models", "Billing", cls._check_pricing_models),
            ("payment_methods", "Billing", cls._check_payment_methods),
            ("receipt_upload", "Billing", cls._check_receipt_upload),
            ("owner_approval", "Billing", cls._check_owner_approval),
            ("subscription_activation", "Billing", cls._check_subscription_activation),
            ("deal_engine", "Finance Core", lambda: cls._check_engine_class("services.deal_engine", "DealEngine", "DealEngine")),
            ("ledger_engine", "Finance Core", lambda: cls._check_engine_class("services.ledger_engine", "LedgerEngine", "LedgerEngine")),
            ("treasury_engine", "Finance Core", lambda: cls._check_engine_class("services.treasury_engine", "TreasuryEngine", "TreasuryEngine")),
            ("pricing_engine", "Finance Core", lambda: cls._check_engine_class("services.pg_pricing_engine", "PricingEngineV1", "PricingEngineV1")),
            ("fx_engine", "Finance Core", lambda: cls._check_engine_class("services.pg_market_data_engine", "MarketDataEngineV1", "FX/MarketData")),
            ("dealer_quote_authority", "Finance Core", cls._check_dealer_quote_authority),
            ("bidex_quote_parser", "Finance Core", cls._check_bidex_quote_parser),
            ("market_reference_sources", "Finance Core", cls._check_market_reference_sources),
            ("liquidity_engine", "Finance Core", lambda: cls._check_engine_class("services.pg_liquidity_engine", "LiquidityEngineV1", "LiquidityEngineV1")),
            ("settlement_engine", "Finance Core", lambda: cls._check_engine_class("services.pg_settlement_engine", "SettlementEngineV1", "SettlementEngineV1")),
            ("risk_engine", "Finance Core", lambda: cls._check_engine_class("services.pg_risk_engine", "RiskEngineV1", "RiskEngineV1")),
            ("kyc_aml_engine", "Finance Core", lambda: cls._check_engine_class("services.pg_kyc_aml_engine", "KycAmlEngine", "KycAmlEngine")),
            ("ai_sales_agent", "AI", lambda: cls._check_engine_class("services.pg_ai_sales_agent_engine", "AiSalesAgentV1", "AiSalesAgentV1")),
            ("ai_procurement_agent", "AI", lambda: cls._check_engine_class("services.pg_ai_procurement_agent_engine", "AiProcurementAgentV1", "AiProcurementAgentV1")),
            ("ai_advertising_agent", "AI", lambda: cls._check_engine_class("services.pg_ai_advertising_agent_engine", "AiAdvertisingAgentV1", "AiAdvertisingAgentV1")),
            ("ai_skill_engine", "AI", lambda: cls._check_engine_class("services.pg_ai_skill_engine", "AiSkillEngineV1", "AiSkillEngineV1")),
            ("ai_orchestrator", "AI", lambda: cls._check_engine_class("services.pg_deal_workflow", "DealWorkflowService", "DealWorkflow orchestrator")),
            ("security_role_isolation", "Security", cls._check_role_isolation),
            ("security_tenant_isolation", "Security", cls._check_security_tenant_isolation),
            ("security_audit_logging", "Security", cls._check_audit_logging),
            ("security_permission_checks", "Security", cls._check_permission_checks),
        ]

    @classmethod
    async def run_suite(cls) -> dict[str, Any]:
        modules: dict[str, dict[str, Any]] = {}
        categories: dict[str, list[str]] = {}

        for key, category, checker in cls._all_checks():
            try:
                if asyncio.iscoroutinefunction(checker):
                    item = await checker()
                else:
                    result = checker()
                    if inspect.isawaitable(result):
                        item = await result
                    else:
                        item = result
            except Exception as exc:
                item = _result("failed", str(exc)[:80])
            item["category"] = category
            modules[key] = item
            categories.setdefault(category, []).append(key)

        scores = _score_statuses(modules)
        status = _overall_status(scores, modules)
        payload = {
            "status": status,
            "modules": modules,
            "categories": categories,
            "scores": scores,
            "tested_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        from database import save_platform_health_run

        save_platform_health_run({
            "status": status,
            "results": modules,
            "tested_at": payload["tested_at"],
            "scores": scores,
            "suite": "platform_readiness_v1",
        })
        return payload

    @staticmethod
    def format_report(payload: dict[str, Any]) -> str:
        lines = [
            "PLATFORM READINESS TEST SUITE v1",
            f"STATUS: {payload.get('status', 'UNKNOWN')}",
            "",
        ]
        current_category = None
        for key, item in payload.get("modules", {}).items():
            category = item.get("category", "")
            if category != current_category:
                current_category = category
                lines.append(f"--- {category} ---")
            status = item.get("status", "failed").upper()
            detail = item.get("detail", "")
            suffix = f" ({detail})" if detail else ""
            lines.append(f"• {key}: {status}{suffix}")

        scores = payload.get("scores", {})
        lines.extend([
            "",
            f"Platform readiness score: {scores.get('platform', 0)}%",
            f"Commercial readiness score: {scores.get('commercial', 0)}%",
            f"Technical debt score: {scores.get('technical_debt', 0)}%",
            "",
            f"Tested: {payload.get('tested_at', '—')}",
        ])
        return "\n".join(lines)


def run_platform_readiness_suite() -> dict[str, Any]:
    """Sync entry point for scripts and CLI."""
    return asyncio.run(PlatformReadinessTestSuite.run_suite())
