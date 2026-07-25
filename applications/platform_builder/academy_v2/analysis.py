"""Live builder analysis & business impact — Sprint 28.6."""

from __future__ import annotations

from typing import Any


def analyze_builder(draft: dict[str, Any] | None = None, *, builder_id: str = "generic") -> dict[str, Any]:
    draft = draft or {}
    strengths = []
    missing = []
    optimizations = []
    future = []

    if draft.get("name"):
        strengths.append("Named configuration")
    else:
        missing.append("Name")

    modules = draft.get("modules") or []
    if len(modules) >= 3:
        strengths.append("Solid module coverage")
    elif modules:
        optimizations.append("Expand modules to at least CRM + Knowledge + Analytics")
    else:
        missing.append("Modules")

    if draft.get("ai_team") or draft.get("ai_mode"):
        strengths.append("AI connected")
    else:
        missing.append("AI Team")
        future.append("Connect AI Team Center specialists")

    if draft.get("knowledge_topics") or "knowledge_base" in modules:
        strengths.append("Knowledge ready")
    else:
        missing.append("Knowledge Sources")
        optimizations.append("Attach SOPs before go-live")

    if draft.get("dashboard_widgets"):
        strengths.append("Dashboard widgets selected")
    else:
        future.append("Add Organization Map widget for AI Ops readiness")

    if not optimizations:
        optimizations.append("Run a Concierge morning briefing after create")
    if not future:
        future.append("Enable Marketplace Apps when ready to expand")

    score = max(0, 100 - len(missing) * 15 - max(0, 3 - len(modules)) * 5)
    return {
        "builder_id": builder_id,
        "strengths": strengths,
        "missing_components": missing,
        "optimization_ideas": optimizations,
        "future_recommendations": future,
        "readiness_score": score,
        "ready": score >= 70,
    }


def business_impact(option_id: str, option_name: str | None = None) -> dict[str, Any]:
    name = option_name or option_id.replace("_", " ").title()
    return {
        "option_id": option_id,
        "option_name": name,
        "business_value": f"{name} improves operational clarity and decision speed.",
        "expected_benefits": f"Teams spend less time searching and more time executing with {name}.",
        "typical_industry_usage": f"Commonly adopted across clinics, retail, and professional services for {name}.",
        "estimated_impact": "Medium–High within the first 30 days after activation.",
    }
