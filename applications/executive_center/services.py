"""AI Executive Assistant + Analytics + Visualization + Enterprise (Sprint 12.3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.executive_center.shared.exceptions import ValidationError
from applications.executive_center.shared.store import ExecutiveCenterStore, executive_center_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutiveAI:
    def __init__(self, store: ExecutiveCenterStore | None = None) -> None:
        self.store = store or executive_center_store

    def _session(self, *, agent: str, query: str, response: dict[str, Any]) -> dict[str, Any]:
        sid = f"exai_{uuid.uuid4().hex[:10]}"
        row = {"session_id": sid, "agent": agent, "query": query, "response": response, "at": _now()}
        self.store.ai_sessions.save(sid, row)
        return row

    def ceo_assistant(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        response = {
            "role": "ceo_assistant",
            "advice": "Align capital allocation with highest-ROI platforms; prioritize safety and certification.",
            "context": dict(context or {}),
            "policy": "executive_assistance_only",
        }
        return self._session(agent="ceo_assistant", query=query, response=response)

    def project_assistant(self, *, query: str, project_id: str = "") -> dict[str, Any]:
        response = {"role": "project_assistant", "project_id": project_id, "advice": "Track blockers weekly; keep twin sync healthy."}
        return self._session(agent="project_assistant", query=query, response=response)

    def business_advisor(self, *, query: str) -> dict[str, Any]:
        response = {"role": "business_advisor", "advice": "Expand marketplace connectors where utilization exceeds 70%."}
        return self._session(agent="business_advisor", query=query, response=response)

    def risk_analysis(self, *, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        s = dict(signals or {})
        score = 20
        if float(s.get("failure_rate", 0)) > 0.1:
            score += 30
        if float(s.get("cpu_pct", 0)) > 85:
            score += 20
        level = "high" if score >= 50 else "medium" if score >= 30 else "low"
        response = {"risk_score": score, "risk_level": level, "signals": s}
        return self._session(agent="risk_analysis", query="risk", response=response)

    def recommendations(self, *, focus: str = "growth") -> dict[str, Any]:
        response = {
            "focus": focus,
            "recommendations": [
                "Increase twin coverage for mission-critical apps",
                "Publish executive weekly report automation",
                "Review agent cost estimates in workflow studio",
            ],
        }
        return self._session(agent="recommendations", query=focus, response=response)

    def forecasting(self, *, metric: str = "revenue", horizon_days: int = 30) -> dict[str, Any]:
        response = {"metric": metric, "horizon_days": horizon_days, "forecast": [1.0, 1.03, 1.07, 1.1], "unit": "index"}
        return self._session(agent="forecasting", query=metric, response=response)

    def executive_report(self, *, period: str = "weekly") -> dict[str, Any]:
        rid = f"erpt_{uuid.uuid4().hex[:10]}"
        report = {
            "report_id": rid,
            "period": period,
            "sections": ["kpis", "risks", "twins", "ai", "infrastructure", "recommendations"],
            "status": "generated",
            "at": _now(),
        }
        self.store.reports.save(rid, report)
        return self._session(agent="executive_report", query=period, response=report)

    def strategic_planning(self, *, goals: list[str] | None = None) -> dict[str, Any]:
        response = {
            "goals": list(goals or ["scale ecosystem", "certify platforms", "grow marketplace"]),
            "plan": ["Stabilize", "Integrate", "Scale", "Optimize"],
        }
        return self._session(agent="strategic_planning", query="plan", response=response)

    def assist(self, *, agent: str, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        key = agent.lower().replace("-", "_")
        dispatch = {
            "ceo_assistant": lambda: self.ceo_assistant(query=query, context=ctx),
            "project_assistant": lambda: self.project_assistant(query=query, project_id=ctx.get("project_id", "")),
            "business_advisor": lambda: self.business_advisor(query=query),
            "risk_analysis": lambda: self.risk_analysis(signals=ctx.get("signals") or ctx),
            "recommendations": lambda: self.recommendations(focus=query or ctx.get("focus", "growth")),
            "forecasting": lambda: self.forecasting(metric=ctx.get("metric", "revenue"), horizon_days=int(ctx.get("horizon_days", 30))),
            "executive_report": lambda: self.executive_report(period=query or "weekly"),
            "strategic_planning": lambda: self.strategic_planning(goals=ctx.get("goals")),
        }
        if key not in dispatch:
            raise ValidationError(f"unknown executive agent: {agent}")
        return dispatch[key]()

    def status(self) -> dict[str, Any]:
        return {"executive_ai": "1.0", "sessions": len(self.store.ai_sessions.list_all()), "ready": True}


class ExecutiveAnalytics:
    def __init__(self, store: ExecutiveCenterStore | None = None) -> None:
        self.store = store or executive_center_store

    def run(self, *, domain: str = "business") -> dict[str, Any]:
        domains = {
            "business",
            "financial",
            "ai",
            "agent",
            "workflow",
            "marketplace",
            "knowledge",
            "infrastructure",
        }
        if domain not in domains:
            raise ValidationError(f"domain must be one of {sorted(domains)}")
        aid = f"an_{uuid.uuid4().hex[:10]}"
        row = {
            "analytics_id": aid,
            "domain": domain,
            "kpis": {
                "score": 0.82,
                "trend": "up",
                "samples": len(self.store.metrics.list_all()) + len(self.store.infra_samples.list_all()),
            },
            "at": _now(),
        }
        self.store.analytics.save(aid, row)
        return row

    def all_domains(self) -> dict[str, Any]:
        return {d: self.run(domain=d) for d in ("business", "financial", "ai", "agent", "workflow", "marketplace", "knowledge", "infrastructure")}

    def status(self) -> dict[str, Any]:
        return {"analytics": "1.0", "reports": len(self.store.analytics.list_all()), "ready": True}


class ExecutiveVisualization:
    def __init__(self, store: ExecutiveCenterStore | None = None) -> None:
        self.store = store or executive_center_store

    def _graph(self, graph_type: str, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
        gid = f"graph_{uuid.uuid4().hex[:8]}"
        row = {"graph_id": gid, "type": graph_type, "nodes": nodes, "edges": edges, "at": _now()}
        self.store.graphs.save(gid, row)
        return row

    def organization_graph(self) -> dict[str, Any]:
        orgs = self.store.organizations.list_all()
        nodes = [{"id": o.get("org_id"), "label": o.get("name")} for o in orgs] or [{"id": "org_root", "label": "Enterprise"}]
        return self._graph("organization_graph", nodes, [])

    def knowledge_graph(self) -> dict[str, Any]:
        return self._graph(
            "knowledge_graph",
            [{"id": "kg", "label": "Global Knowledge"}, {"id": "drone", "label": "Drone KB"}, {"id": "market", "label": "Marketplace KB"}],
            [{"from": "kg", "to": "drone"}, {"from": "kg", "to": "market"}],
        )

    def agent_graph(self) -> dict[str, Any]:
        return self._graph(
            "agent_graph",
            [{"id": "chief", "label": "Chief AI"}, {"id": "ceo", "label": "CEO Assistant"}, {"id": "drone", "label": "Drone AI"}],
            [{"from": "chief", "to": "ceo"}, {"from": "chief", "to": "drone"}],
        )

    def workflow_graph(self) -> dict[str, Any]:
        return self._graph("workflow_graph", [{"id": "wf1", "label": "Executive Automation"}], [])

    def infrastructure_graph(self) -> dict[str, Any]:
        return self._graph(
            "infrastructure_graph",
            [{"id": "cluster", "label": "Primary"}, {"id": "api", "label": "API Gateway"}],
            [{"from": "cluster", "to": "api"}],
        )

    def digital_twin_visualization(self, twins: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        twins = twins or self.store.twins.list_all()
        nodes = [{"id": t.get("twin_id"), "label": t.get("name"), "type": t.get("twin_type")} for t in twins]
        return self._graph("digital_twin_visualization", nodes, [])

    def live_charts(self) -> dict[str, Any]:
        samples = self.store.infra_samples.list_all()[-20:]
        return {"type": "live_charts", "series": [{"t": s.get("at"), "cpu": s.get("cpu_pct"), "ram": s.get("ram_pct")} for s in samples]}

    def heat_maps(self) -> dict[str, Any]:
        return {"type": "heat_maps", "cells": [{"x": "api", "y": "latency", "v": 0.4}, {"x": "agents", "y": "load", "v": 0.6}]}

    def timelines(self) -> dict[str, Any]:
        feed = self.store.activity.list_all()[-30:]
        return {"type": "timelines", "events": feed}

    def interactive_bundle(self) -> dict[str, Any]:
        return {
            "organization": self.organization_graph(),
            "knowledge": self.knowledge_graph(),
            "agents": self.agent_graph(),
            "workflows": self.workflow_graph(),
            "infrastructure": self.infrastructure_graph(),
            "twins": self.digital_twin_visualization(),
            "charts": self.live_charts(),
            "heatmaps": self.heat_maps(),
            "timelines": self.timelines(),
        }

    def status(self) -> dict[str, Any]:
        return {"visualization": "1.0", "graphs": len(self.store.graphs.list_all()), "ready": True}


class EnterpriseControl:
    def __init__(self, store: ExecutiveCenterStore | None = None) -> None:
        self.store = store or executive_center_store

    def register_company(self, *, name: str, region: str = "global") -> dict[str, Any]:
        cid = f"co_{uuid.uuid4().hex[:10]}"
        row = {"company_id": cid, "name": name, "region": region, "at": _now()}
        self.store.companies.save(cid, row)
        return row

    def register_organization(self, *, company_id: str, name: str) -> dict[str, Any]:
        oid = f"org_{uuid.uuid4().hex[:10]}"
        row = {"org_id": oid, "company_id": company_id, "name": name, "at": _now()}
        self.store.organizations.save(oid, row)
        return row

    def register_region(self, *, company_id: str, name: str, code: str = "") -> dict[str, Any]:
        rid = f"reg_{uuid.uuid4().hex[:8]}"
        row = {"region_id": rid, "company_id": company_id, "name": name, "code": code or name[:3].upper(), "at": _now()}
        self.store.regions.save(rid, row)
        return row

    def grant_permission(self, *, principal: str, role: str, scope: str = "global") -> dict[str, Any]:
        if role not in {"executive", "ops", "analyst", "viewer"}:
            raise ValidationError("role must be executive|ops|analyst|viewer")
        pid = f"perm_{uuid.uuid4().hex[:8]}"
        row = {"permission_id": pid, "principal": principal, "role": role, "scope": scope, "at": _now()}
        self.store.permissions.save(pid, row)
        return row

    def role_based_dashboard(self, *, role: str) -> dict[str, Any]:
        mapping = {
            "executive": ["global", "finance", "ai"],
            "ops": ["operations", "ai"],
            "analyst": ["finance", "ai"],
            "viewer": ["global"],
        }
        return {"role": role, "dashboards": mapping.get(role, ["global"])}

    def audit(self, *, actor: str, action: str, resource: str = "") -> dict[str, Any]:
        aid = f"aud_{uuid.uuid4().hex[:10]}"
        row = {"audit_id": aid, "actor": actor, "action": action, "resource": resource, "at": _now()}
        self.store.audits.save(aid, row)
        return row

    def audit_report(self) -> dict[str, Any]:
        return {"audits": self.store.audits.list_all(), "count": len(self.store.audits.list_all())}

    def executive_report_pack(self) -> dict[str, Any]:
        return {
            "companies": len(self.store.companies.list_all()),
            "organizations": len(self.store.organizations.list_all()),
            "regions": len(self.store.regions.list_all()),
            "permissions": len(self.store.permissions.list_all()),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "enterprise": "1.0",
            "companies": len(self.store.companies.list_all()),
            "organizations": len(self.store.organizations.list_all()),
            "ready": True,
        }


executive_ai = ExecutiveAI()
executive_analytics = ExecutiveAnalytics()
executive_visualization = ExecutiveVisualization()
enterprise_control = EnterpriseControl()
