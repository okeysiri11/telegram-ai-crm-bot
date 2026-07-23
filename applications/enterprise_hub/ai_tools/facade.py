"""AI Tools & Skills Suite facade — Sprint 20.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_tools.audit import ToolAudit
from applications.enterprise_hub.ai_tools.execution_context import ExecutionContext
from applications.enterprise_hub.ai_tools.marketplace.installer import MarketplaceInstaller
from applications.enterprise_hub.ai_tools.marketplace.packages import PackageCatalog
from applications.enterprise_hub.ai_tools.marketplace.signatures import PackageSignatures
from applications.enterprise_hub.ai_tools.policy import ToolPolicyEngine
from applications.enterprise_hub.ai_tools.sandbox import Sandbox
from applications.enterprise_hub.ai_tools.skill_manager import SkillManager
from applications.enterprise_hub.ai_tools.skill_registry import SkillRegistry
from applications.enterprise_hub.ai_tools.skills.contract_review import ContractReviewSkill
from applications.enterprise_hub.ai_tools.skills.document_processing import DocumentProcessingSkill
from applications.enterprise_hub.ai_tools.skills.forecasting import ForecastingSkill
from applications.enterprise_hub.ai_tools.skills.report_generation import ReportGenerationSkill
from applications.enterprise_hub.ai_tools.skills.scheduling import SchedulingSkill
from applications.enterprise_hub.ai_tools.tool_executor import ToolExecutor
from applications.enterprise_hub.ai_tools.tool_manager import ToolManager
from applications.enterprise_hub.ai_tools.tool_registry import ToolRegistry
from applications.enterprise_hub.ai_tools.tool_router import ToolRouter
from applications.enterprise_hub.ai_tools.tools.analytics.actions import AnalyticsTool
from applications.enterprise_hub.ai_tools.tools.browser.actions import BrowserTool
from applications.enterprise_hub.ai_tools.tools.communication.actions import CommunicationTool
from applications.enterprise_hub.ai_tools.tools.crm.actions import CrmTool
from applications.enterprise_hub.ai_tools.tools.custom.actions import CustomTool
from applications.enterprise_hub.ai_tools.tools.erp.actions import ErpTool
from applications.enterprise_hub.ai_tools.tools.files.actions import FilesTool
from applications.enterprise_hub.ai_tools.tools.finance.actions import FinanceTool
from applications.enterprise_hub.ai_tools.tools.integrations.actions import IntegrationsTool
from applications.enterprise_hub.ai_tools.tools.legal.actions import LegalTool
from applications.enterprise_hub.ai_tools.tools.terminal.actions import TerminalTool
from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIToolsSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = ToolRegistry(self.store)
        self.tools = ToolManager(self.store)
        self.executor = ToolExecutor(self.store)
        self.router = ToolRouter(self.store)
        self.skills = SkillManager(self.store)
        self.skill_registry = SkillRegistry(self.store)
        self.context = ExecutionContext(self.store)
        self.sandbox = Sandbox(self.store)
        self.policy = ToolPolicyEngine(self.store)
        self.audit = ToolAudit(self.store)
        self.packages = PackageCatalog(self.store)
        self.signatures = PackageSignatures(self.store)
        self.marketplace = MarketplaceInstaller(self.store)
        self.crm = CrmTool(self.store)
        self.erp = ErpTool(self.store)
        self.finance = FinanceTool(self.store)
        self.legal = LegalTool(self.store)
        self.analytics_tools = AnalyticsTool(self.store)
        self.files = FilesTool(self.store)
        self.communication = CommunicationTool(self.store)
        self.integrations = IntegrationsTool(self.store)
        self.browser = BrowserTool(self.store)
        self.terminal = TerminalTool(self.store)
        self.custom = CustomTool(self.store)
        self.document_processing = DocumentProcessingSkill(self.store)
        self.report_generation = ReportGenerationSkill(self.store)
        self.contract_review = ContractReviewSkill(self.store)
        self.forecasting = ForecastingSkill(self.store)
        self.scheduling = SchedulingSkill(self.store)

    def analytics(self) -> dict[str, Any]:
        tools = self.store.ats_tools.list_all()
        contexts = self.store.ats_contexts.list_all()
        skills = self.store.ats_skills.list_all()
        completed = [c for c in contexts if c.get("status") == "completed"]
        failed = [c for c in contexts if c.get("status") == "failed"]
        total_cost = sum(float(c.get("cost", 0) or 0) for c in contexts)
        avg_duration = (
            sum(int(c.get("duration_ms", 0) or 0) for c in completed) / len(completed) if completed else 0
        )
        top_tools = sorted(tools, key=lambda t: t.get("usage_count", 0), reverse=True)[:5]
        skill_ratings = sorted(skills, key=lambda s: s.get("rating", 0), reverse=True)
        aid = _id("ats_an")
        return self.store.ats_analytics.save(
            aid,
            {
                "analytics_id": aid,
                "top_tools": [{"tool_id": t["tool_id"], "name": t["name"], "usage": t.get("usage_count", 0)} for t in top_tools],
                "success_rate": (len(completed) / len(contexts)) if contexts else 1.0,
                "avg_duration_ms": avg_duration,
                "total_cost": total_cost,
                "errors": len(failed),
                "skill_ratings": [{"skill_id": s["skill_id"], "name": s["name"], "rating": s.get("rating")} for s in skill_ratings],
                "recommendations": ["prefer lower-cost tools when quality equal"] if top_tools else ["register tools"],
                "at": _now(),
            },
        )

    def bootstrap(self) -> dict[str, Any]:
        pol = self.policy.define(
            name="default-tools",
            allowed_agents=["*"],
            allowed_roles=["admin", "agent", "operator"],
            allowed_domains=["*"],
            max_cost=5.0,
            require_confirmation=False,
        )

        t_crm = self.crm.register(name="crm.save_deal", description="Save deal to CRM", permissions=["read", "write", "execute"])
        t_legal = self.legal.register(name="legal.risk_check", description="Check legal risks", cost_per_call=0.05)
        t_files = self.files.register(name="files.fetch_contract", description="Fetch contract file")
        t_comm = self.communication.register(name="comms.notify_manager", description="Notify manager")
        t_fin = self.finance.register(name="finance.analyze", description="Financial analysis", cost_per_call=0.04)
        t_an = self.analytics_tools.register(name="analytics.report", description="Build analytics report")
        t_erp = self.erp.register(name="erp.sync", description="ERP sync")
        t_int = self.integrations.register(name="integrations.webhook", description="Call webhook", permissions=["execute", "network"])
        t_br = self.browser.register(name="browser.open", description="Open URL", permissions=["execute", "network"])
        t_term = self.terminal.register(name="terminal.run", description="Sandboxed command", permissions=["execute"])
        t_custom = self.custom.register(name="custom.hook", description="Custom tool")

        skill_contract = self.contract_review.register(
            steps=[
                {"tool_id": t_files["tool_id"], "params": {"doc": "contract"}},
                {"tool_id": t_legal["tool_id"], "params": {"mode": "risks"}},
                {"tool_id": t_comm["tool_id"], "params": {"channel": "manager"}},
                {"tool_id": t_crm["tool_id"], "params": {"entity": "deal"}},
            ]
        )
        skill_report = self.report_generation.register(
            steps=[
                {"tool_id": t_fin["tool_id"]},
                {"tool_id": t_an["tool_id"]},
            ]
        )
        skill_doc = self.document_processing.register(steps=[{"tool_id": t_files["tool_id"]}])
        skill_fc = self.forecasting.register(steps=[{"tool_id": t_fin["tool_id"]}, {"tool_id": t_an["tool_id"]}])
        skill_sch = self.scheduling.register(steps=[{"tool_id": t_comm["tool_id"]}])

        run_tool = self.executor.execute(
            tool_id=t_crm["tool_id"],
            params={"deal": "ACME"},
            agent_id="crm_agent",
            user_id="user_1",
        )
        run_skill = self.skills.run(
            skill_id=skill_contract["skill_id"],
            agent_id="legal_agent",
            user_id="user_1",
            params={"contract_id": "C-100"},
        )

        pkg = self.packages.publish(
            name="extra-crm-tool",
            kind="tool",
            version="1.0.1",
            payload={"name": "crm.note", "domain": "crm", "description": "Add note"},
        )
        sig = self.signatures.sign(package_id=pkg["package_id"])
        inst = self.marketplace.install(package_id=pkg["package_id"], signature_id=sig["signature_id"])

        route = self.router.resolve(name="crm.save_deal")
        analytics = self.analytics()

        return {
            "bootstrap": True,
            "policy_id": pol["policy_id"],
            "tool_crm_id": t_crm["tool_id"],
            "tool_legal_id": t_legal["tool_id"],
            "tool_files_id": t_files["tool_id"],
            "tool_comm_id": t_comm["tool_id"],
            "tool_finance_id": t_fin["tool_id"],
            "tool_analytics_id": t_an["tool_id"],
            "tool_erp_id": t_erp["tool_id"],
            "tool_integrations_id": t_int["tool_id"],
            "tool_browser_id": t_br["tool_id"],
            "tool_terminal_id": t_term["tool_id"],
            "tool_custom_id": t_custom["tool_id"],
            "skill_contract_id": skill_contract["skill_id"],
            "skill_report_id": skill_report["skill_id"],
            "skill_document_id": skill_doc["skill_id"],
            "skill_forecast_id": skill_fc["skill_id"],
            "skill_schedule_id": skill_sch["skill_id"],
            "execution_context_id": run_tool["context_id"],
            "skill_run_cost": run_skill["total_cost"],
            "package_id": pkg["package_id"],
            "signature_id": sig["signature_id"],
            "install_id": inst["install_id"],
            "route_id": route["route_id"],
            "analytics_id": analytics["analytics_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "tools": self.tools.status(),
            "skills": self.skills.status(),
            "policy": self.policy.status(),
            "audit": self.audit.status(),
            "packages": self.store.ats_packages.count(),
            "contexts": self.store.ats_contexts.count(),
        }


ai_tools = AIToolsSuite()
