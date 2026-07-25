"""Enterprise Organization Brain library — Sprint 27.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_organization_brain.models import (
    API_PREFIX,
    ARCHITECTURE,
    DEPARTMENTS,
    EXECUTIVE_BOARD,
    HUB,
    KPI_TARGETS,
    KNOWLEDGE_KINDS,
    ORG_ENTITY_TYPES,
    PRINCIPLES,
    SPRINT,
    VERSION,
    WEB_PATH,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class OrganizationBrainLibrary:
    """Digital intelligence of the company — org structure, board, decisions."""

    def __init__(self) -> None:
        self._org = self._seed_organization()
        self._board = self._seed_board()
        self._departments = self._seed_departments()
        self._knowledge: list[dict[str, Any]] = self._seed_knowledge()
        self._decisions: list[dict[str, Any]] = []
        self._meetings: list[dict[str, Any]] = []
        self._orchestrations: list[dict[str, Any]] = []
        self._alerts: list[dict[str, Any]] = [
            {"level": "info", "message": "Q3 pipeline review scheduled"},
            {"level": "warn", "message": "Logistics capacity at 86%"},
        ]
        self._recommendations: list[str] = [
            "Reallocate AI agents to Sales outreach this week",
            "Approve Manufacturing overtime budget for peak demand",
        ]

    def _seed_organization(self) -> dict[str, Any]:
        holding_id = "hold_alpha"
        company_id = "co_platform"
        org_id = "org_enterprise"
        return {
            "holdings": [
                {
                    "id": holding_id,
                    "name": "Alpha Holdings",
                    "children": [company_id],
                }
            ],
            "companies": [
                {
                    "id": company_id,
                    "name": "Enterprise AI Platform Inc.",
                    "holding_id": holding_id,
                    "organizations": [org_id],
                }
            ],
            "organizations": [
                {
                    "id": org_id,
                    "name": "Core Operations",
                    "company_id": company_id,
                    "departments": [f"dept_{d.lower().replace(' ', '_')}" for d in DEPARTMENTS],
                }
            ],
            "departments": [],
            "teams": [
                {"id": "team_growth", "name": "Growth Squad", "department": "Sales", "members": 6},
                {"id": "team_ops", "name": "Ops Core", "department": "Logistics", "members": 8},
                {"id": "team_ai", "name": "AI Lab", "department": "AI Department", "members": 5},
            ],
            "employees": [
                {"id": "emp_ceo", "name": "Alex Rivera", "role": "CEO", "load": 0.72},
                {"id": "emp_cfo", "name": "Sam Chen", "role": "CFO", "load": 0.65},
                {"id": "emp_ops", "name": "Jordan Lee", "role": "Ops Lead", "load": 0.81},
            ],
            "contractors": [
                {"id": "ctr_legal", "name": "North Counsel LLP", "domain": "Legal", "load": 0.4},
            ],
            "roles": [
                {"id": "role_exec", "name": "Executive", "level": 1},
                {"id": "role_mgr", "name": "Manager", "level": 2},
                {"id": "role_ic", "name": "Individual Contributor", "level": 3},
            ],
            "positions": [
                {"id": "pos_ceo", "title": "Chief Executive Officer", "role": "Executive"},
                {"id": "pos_analyst", "title": "Business Analyst", "role": "Individual Contributor"},
            ],
            "hierarchy": {
                "holding": holding_id,
                "company": company_id,
                "organization": org_id,
                "depth": 4,
            },
        }

    def _seed_board(self) -> list[dict[str, Any]]:
        domains = {
            "CEO": "strategy_governance",
            "COO": "operations_delivery",
            "CFO": "finance_capital",
            "CTO": "technology_platform",
            "CMO": "growth_brand",
            "CHRO": "people_culture",
            "CLO": "legal_compliance",
        }
        board = []
        for title in EXECUTIVE_BOARD:
            board.append(
                {
                    "agent_id": f"board_{title.lower()}",
                    "title": title,
                    "name": f"{title} AI",
                    "domain": domains[title],
                    "status": "active",
                    "load": 0.35 if title != "COO" else 0.58,
                    "authority": "executive",
                }
            )
        return board

    def _seed_departments(self) -> list[dict[str, Any]]:
        depts = []
        for name in DEPARTMENTS:
            code = name.lower().replace(" ", "_")
            depts.append(
                {
                    "id": f"dept_{code}",
                    "name": name,
                    "status": "operational",
                    "efficiency": 0.78 if name != "Logistics" else 0.64,
                    "headcount": 12 if name not in ("AI Department", "Legal") else 5,
                    "ai_load": 0.4 if name == "AI Department" else 0.22,
                    "kpi_score": 82 if name != "Logistics" else 71,
                    "owner_ai": "COO AI" if name != "Finance" else "CFO AI",
                }
            )
        self._org["departments"] = [{"id": d["id"], "name": d["name"]} for d in depts]
        return depts

    def _seed_knowledge(self) -> list[dict[str, Any]]:
        samples = [
            ("structure", "Company hierarchy: Holding → Company → Org → Departments"),
            ("regulations", "All departments follow Enterprise Control Framework v3"),
            ("job_instructions", "Department leads file weekly KPI packs by Friday 17:00"),
            ("policies", "AI agents require human approval for spend > $10k"),
            ("kpi", "North-star: ARR growth 25%, NPS ≥ 45, AI utilization ≥ 60%"),
            ("business_processes", "Lead → Quote → Contract → Fulfillment → Revenue recognition"),
        ]
        return [
            {"id": _id("okg"), "kind": kind, "content": content, "created_at": _now()}
            for kind, content in samples
        ]

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        return {
            "bootstrap": True,
            "version": VERSION,
            "sprint": SPRINT,
            "hub": HUB,
            "api_prefix": API_PREFIX,
            "web_path": WEB_PATH,
            "organization_model_ready": True,
            "executive_board_ready": True,
            "department_orchestration_ready": True,
            "decision_engine_ready": True,
            "executive_meetings_ready": True,
            "organization_knowledge_ready": True,
            "executive_dashboard_ready": True,
            "architecture": list(ARCHITECTURE),
            "full": {
                "inventory": self.inventory(),
                "dashboard": self.dashboard(),
                "organization": self.organization_model(),
                "board": self.executive_board(),
                "departments": self.departments(),
                "knowledge": self.knowledge_list(),
                "links": {
                    "ai_os": "/api/ai-os/v1",
                    "command_center": "/api/enterprise-command/v1",
                    "navigation": "/api/enterprise-navigation/v1",
                },
            },
        }

    def inventory(self) -> dict[str, Any]:
        return {
            "hub": HUB,
            "version": VERSION,
            "sprint": SPRINT,
            "architecture": list(ARCHITECTURE),
            "entity_types": list(ORG_ENTITY_TYPES),
            "board_roles": list(EXECUTIVE_BOARD),
            "departments": list(DEPARTMENTS),
            "knowledge_kinds": list(KNOWLEDGE_KINDS),
            "principles": list(PRINCIPLES),
            "kpi_targets": dict(KPI_TARGETS),
            "counts": {
                "board": len(self._board),
                "departments": len(self._departments),
                "employees": len(self._org["employees"]),
                "knowledge": len(self._knowledge),
                "meetings": len(self._meetings),
                "decisions": len(self._decisions),
            },
        }

    def organization_model(self) -> dict[str, Any]:
        return {
            "ready": True,
            "entity_types": list(ORG_ENTITY_TYPES),
            **self._org,
        }

    def executive_board(self) -> dict[str, Any]:
        return {
            "ready": True,
            "count": len(self._board),
            "members": list(self._board),
        }

    def departments(self) -> dict[str, Any]:
        return {
            "ready": True,
            "count": len(self._departments),
            "items": list(self._departments),
        }

    def orchestrate_department(self, department: str, objective: str | None = None) -> dict[str, Any]:
        match = next(
            (d for d in self._departments if d["name"].lower() == department.lower() or d["id"] == department),
            None,
        )
        if not match:
            # soft create for unknown names used in tests/API
            match = {
                "id": f"dept_{department.lower().replace(' ', '_')}",
                "name": department,
                "status": "orchestrating",
                "efficiency": 0.7,
                "headcount": 4,
                "ai_load": 0.3,
                "kpi_score": 75,
                "owner_ai": "COO AI",
            }
        tasks = [
            {"task": "assess_capacity", "owner": match["owner_ai"], "status": "done"},
            {"task": "assign_squad", "owner": match["name"], "status": "done"},
            {
                "task": "execute_objective",
                "owner": match["name"],
                "status": "in_progress",
                "objective": objective or f"Optimize {match['name']} throughput",
            },
        ]
        record = {
            "orchestration_id": _id("dorch"),
            "ok": True,
            "department": match["name"],
            "objective": objective or f"Optimize {match['name']} throughput",
            "tasks": tasks,
            "status": "running",
            "created_at": _now(),
        }
        self._orchestrations.append(record)
        return record

    def decide(
        self,
        topic: str,
        metrics: dict[str, Any] | None = None,
        *,
        allocate: bool = True,
    ) -> dict[str, Any]:
        metrics = metrics or {"revenue_growth": 0.12, "margin": 0.28, "nps": 41, "risk_index": 0.34}
        risks = []
        if metrics.get("risk_index", 0) > 0.3:
            risks.append("elevated_operational_risk")
        if metrics.get("nps", 50) < 45:
            risks.append("customer_satisfaction_gap")
        proposals = [
            {"id": "p1", "action": "increase_sales_ai_quota", "impact": "high"},
            {"id": "p2", "action": "freeze_non_critical_capex", "impact": "medium"},
            {"id": "p3", "action": "launch_logistics_sprint", "impact": "high"},
        ]
        chosen = proposals[0] if metrics.get("revenue_growth", 0) < 0.2 else proposals[2]
        tasks = [
            {"title": f"Execute: {chosen['action']}", "owner": "COO AI", "kpi": "throughput"},
            {"title": "Track KPI weekly", "owner": "CFO AI", "kpi": "margin"},
        ]
        resources = {
            "budget_usd": 25000 if allocate else 0,
            "ai_slots": 3 if allocate else 0,
            "headcount_flex": 2 if allocate else 0,
        }
        record = {
            "decision_id": _id("dec"),
            "ok": True,
            "topic": topic,
            "metrics": metrics,
            "risks": risks,
            "proposals": proposals,
            "chosen": chosen,
            "tasks": tasks,
            "resources": resources,
            "kpi_controls": ["ARR", "NPS", "AI_utilization", "department_efficiency"],
            "created_at": _now(),
        }
        self._decisions.append(record)
        return record

    def run_meeting(
        self,
        topic: str,
        *,
        proposals: list[str] | None = None,
    ) -> dict[str, Any]:
        proposals = proposals or [
            "Accelerate CRM automation",
            "Expand Manufacturing night shift",
            "Hire two AI specialists",
        ]
        discussion = [
            {"speaker": "CEO AI", "point": f"Frame decision on: {topic}"},
            {"speaker": "CFO AI", "point": "Budget headroom exists for option A"},
            {"speaker": "COO AI", "point": "Ops capacity favors staged rollout"},
            {"speaker": "CTO AI", "point": "Platform readiness is sufficient"},
        ]
        votes = {m["title"]: (1 if m["title"] in ("CEO", "COO", "CTO", "CMO") else 0) for m in self._board}
        # simplify: majority for first proposal
        tally = {p: 0 for p in proposals}
        for i, member in enumerate(self._board):
            pick = proposals[i % len(proposals)]
            tally[pick] += 1
            votes[member["title"]] = pick
        winner = max(tally, key=tally.get)
        owners = [
            {"role": "COO AI", "responsibility": "execution"},
            {"role": "CFO AI", "responsibility": "budget_control"},
            {"role": "CHRO AI", "responsibility": "staffing"},
        ]
        protocol = {
            "summary": f"Board approved «{winner}» for {topic}",
            "agreement": True,
            "dissent": [k for k, v in votes.items() if v != winner],
        }
        record = {
            "meeting_id": _id("mtg"),
            "ok": True,
            "topic": topic,
            "discussion": discussion,
            "votes": votes,
            "tally": tally,
            "decision": winner,
            "protocol": protocol,
            "owners": owners,
            "status": "closed",
            "created_at": _now(),
        }
        self._meetings.append(record)
        return record

    def meetings(self) -> dict[str, Any]:
        return {"count": len(self._meetings), "items": list(self._meetings)}

    def knowledge_write(self, kind: str, content: str) -> dict[str, Any]:
        kind_norm = kind if kind in KNOWLEDGE_KINDS else "policies"
        item = {
            "id": _id("okg"),
            "kind": kind_norm,
            "content": content,
            "created_at": _now(),
        }
        self._knowledge.append(item)
        return {"ok": True, **item}

    def knowledge_list(self, kind: str | None = None) -> dict[str, Any]:
        items = self._knowledge
        if kind:
            items = [k for k in items if k["kind"] == kind]
        by_kind = {k: 0 for k in KNOWLEDGE_KINDS}
        for row in self._knowledge:
            by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
        return {
            "ready": True,
            "kinds": list(KNOWLEDGE_KINDS),
            "counts": by_kind,
            "items": list(items),
        }

    def dashboard(self) -> dict[str, Any]:
        emp_load = sum(e["load"] for e in self._org["employees"]) / max(1, len(self._org["employees"]))
        ai_load = sum(m["load"] for m in self._board) / max(1, len(self._board))
        dept_eff = [
            {"name": d["name"], "efficiency": d["efficiency"], "kpi_score": d["kpi_score"]}
            for d in self._departments
        ]
        return {
            "title": "Organization Executive Dashboard",
            "version": VERSION,
            "sprint": SPRINT,
            "company_state": "healthy",
            "kpi": {
                "arr_growth": 0.18,
                "nps": 42,
                "ai_utilization": 0.61,
                "margin": 0.27,
            },
            "department_efficiency": dept_eff,
            "employee_load_avg": round(emp_load, 3),
            "ai_load_avg": round(ai_load, 3),
            "financials": {
                "revenue_mtd": 1_250_000,
                "opex_mtd": 820_000,
                "cash_runway_months": 14,
            },
            "strategic_goals": [
                "Scale multi-agent OS across departments",
                "Raise NPS to 45+",
                "Automate 40% of CRM ops",
            ],
            "alerts": list(self._alerts),
            "recommendations": list(self._recommendations),
            "board_active": sum(1 for m in self._board if m["status"] == "active"),
            "meetings_closed": len(self._meetings),
            "decisions_count": len(self._decisions),
        }

    def status(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "sprint": SPRINT,
            "hub": HUB,
            "api_prefix": API_PREFIX,
            "board": len(self._board),
            "departments": len(self._departments),
            "knowledge": len(self._knowledge),
            "meetings": len(self._meetings),
            "decisions": len(self._decisions),
            "ready": True,
        }
