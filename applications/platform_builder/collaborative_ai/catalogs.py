"""Collaborative AI / Collective Intelligence catalogs — Sprint 28.8."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "team_creation", "title": "AI Team Creation", "index": 1},
    {"id": "role_assignment", "title": "Role Assignment", "index": 2},
    {"id": "collaborative_session", "title": "Collaborative Session", "index": 3},
    {"id": "task_distribution", "title": "Task Distribution", "index": 4},
    {"id": "shared_knowledge", "title": "Shared Knowledge", "index": 5},
    {"id": "decision_engine", "title": "Decision Engine", "index": 6},
    {"id": "executive_summary", "title": "Executive Summary", "index": 7},
    {"id": "team_performance", "title": "Team Performance", "index": 8},
    {"id": "explain_decision", "title": "Explain Decision", "index": 9},
    {"id": "ai_ops_foundation", "title": "AI Operations Center Foundation", "index": 10},
    {"id": "create", "title": "Create", "index": 11},
]

PRIORITIES = ("critical", "high", "medium", "low")

DEFAULT_SPECIALISTS = (
    {"id": "ai_legal", "name": "Legal Specialist", "profession": "Lawyer"},
    {"id": "ai_finance", "name": "Finance Specialist", "profession": "Finance"},
    {"id": "ai_ops", "name": "Operations Specialist", "profession": "Operations"},
    {"id": "ai_marketing", "name": "Marketing Specialist", "profession": "Marketing"},
)

DEFAULT_CONCIERGE = {"id": "concierge_org", "name": "Organization Concierge"}

ROLE_TEMPLATES = (
    {
        "role": "Lead Analyst",
        "responsibilities": ["Frame the problem", "Synthesize findings"],
        "priority": "high",
        "permissions": ["read_knowledge", "propose_decision"],
        "knowledge_scope": ["policies", "case_history"],
        "expected_output": "Structured analysis memo",
    },
    {
        "role": "Domain Specialist",
        "responsibilities": ["Deep dive on domain facts", "Flag risks"],
        "priority": "medium",
        "permissions": ["read_knowledge", "share_findings"],
        "knowledge_scope": ["domain_kb"],
        "expected_output": "Domain findings brief",
    },
    {
        "role": "Risk Advisor",
        "responsibilities": ["Assess downside", "Propose mitigations"],
        "priority": "high",
        "permissions": ["read_knowledge", "flag_risk"],
        "knowledge_scope": ["compliance", "risk_register"],
        "expected_output": "Risk note",
    },
    {
        "role": "Orchestrator",
        "responsibilities": ["Delegate tasks", "Combine results", "Deliver unified answer"],
        "priority": "critical",
        "permissions": ["assign_task", "collect_results", "publish_summary"],
        "knowledge_scope": ["all_shared"],
        "expected_output": "Unified executive answer",
    },
)

CONSENSUS_STATES = ("forming", "debating", "converging", "reached", "blocked")

PERFORMANCE_METRICS = (
    "Completed Tasks",
    "Average Response Time",
    "Collaboration Quality",
    "Knowledge Usage",
    "Specialist Contribution",
)

EXPLAIN_FIELDS = (
    "why_this_recommendation",
    "business_benefits",
    "alternative_approaches",
    "expected_result",
)

OPS_FOUNDATION_SURFACES = (
    "AI Team Map",
    "Visual Layer",
    "Visual IDs",
    "Live Organization",
    "2D AI City Integration",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "priorities": list(PRIORITIES),
        "default_specialists": [dict(s) for s in DEFAULT_SPECIALISTS],
        "default_concierge": dict(DEFAULT_CONCIERGE),
        "role_templates": [dict(r) for r in ROLE_TEMPLATES],
        "consensus_states": list(CONSENSUS_STATES),
        "performance_metrics": list(PERFORMANCE_METRICS),
        "explain_fields": list(EXPLAIN_FIELDS),
        "ops_foundation_surfaces": list(OPS_FOUNDATION_SURFACES),
        "collective_intelligence_ready": True,
        "decision_engine_ready": True,
        "knowledge_exchange_ready": True,
    }
