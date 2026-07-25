"""Concierge Builder catalogs — Sprint 28.3."""

from __future__ import annotations

from typing import Any


def _help(purpose: str, benefits: str, example: str, what: str = "") -> dict[str, str]:
    return {
        "short_description": what or purpose,
        "purpose": purpose,
        "benefits": benefits,
        "example": example,
        "business_value": benefits,
        "tooltip": purpose,
        "more_information": f"{purpose} {benefits}",
    }


WIZARD_STEPS = [
    {"id": "identity", "title": "Concierge Identity", "index": 1},
    {"id": "role", "title": "Concierge Role", "index": 2},
    {"id": "access", "title": "Organization Access", "index": 3},
    {"id": "orchestration", "title": "AI Orchestration", "index": 4},
    {"id": "proactive", "title": "Proactive Assistance", "index": 5},
    {"id": "owner", "title": "Owner Relationship", "index": 6},
    {"id": "recommendations", "title": "Smart Recommendations", "index": 7},
    {"id": "summary", "title": "Summary", "index": 8},
    {"id": "create", "title": "Create", "index": 9},
]

COMMUNICATION_STYLES = [
    {"id": "business_executive", "name": "Business Executive", "sample": "Good morning. Here is your priority brief for today."},
    {"id": "professional", "name": "Professional", "sample": "I’ve prepared a clear update on today’s key items."},
    {"id": "friendly", "name": "Friendly", "sample": "Happy to help — here’s a simple overview."},
    {"id": "mentor", "name": "Mentor", "sample": "Let’s walk through this together, one step at a time."},
    {"id": "best_friend", "name": "Best Friend", "sample": "I’ve got you — here’s what matters most right now."},
    {"id": "best_girlfriend", "name": "Best Girlfriend", "sample": "I’m right here with you. Let’s make today feel lighter."},
    {"id": "direct", "name": "Direct", "sample": "Three priorities: close the deal, review cash, confirm the meeting."},
    {"id": "without_formalities", "name": "Without Formalities", "sample": "Quick take — here’s what needs attention."},
    {"id": "very_informal", "name": "Very Informal", "sample": "Hey — easy wins for today are right here."},
    {"id": "technical", "name": "Technical", "sample": "Route CRM lead scoring to the Sales specialist, then open analytics."},
    {"id": "calm", "name": "Calm", "sample": "Take a breath. Here’s a steady plan for the morning."},
    {"id": "energetic", "name": "Energetic", "sample": "Let’s go — your opportunities are lining up!"},
]

VOICE_PROFILES = [
    {"id": "warm", "name": "Warm"},
    {"id": "clear", "name": "Clear"},
    {"id": "confident", "name": "Confident"},
    {"id": "soft", "name": "Soft"},
]

AVATARS = [
    {"id": "avatar_exec", "name": "Executive", "emoji": "🧑‍💼"},
    {"id": "avatar_guide", "name": "Guide", "emoji": "🧭"},
    {"id": "avatar_spark", "name": "Spark", "emoji": "✨"},
    {"id": "avatar_shield", "name": "Trusted", "emoji": "🛡️"},
]

ROLES = [
    {
        "id": "executive_assistant",
        "name": "Executive Assistant",
        "help": _help(
            "Supports leadership with schedules, briefs, and follow-ups.",
            "Keeps the owner focused on decisions, not busywork.",
            "Example: prepares a morning meeting pack.",
        ),
    },
    {
        "id": "business_concierge",
        "name": "Business Concierge",
        "help": _help(
            "Guides people across the organization with helpful direction.",
            "Faster answers and smoother handoffs between teams.",
            "Example: routes a contract question to Legal AI.",
        ),
    },
    {
        "id": "personal_concierge",
        "name": "Personal Concierge",
        "help": _help(
            "Stays close to the owner’s preferences and daily rhythm.",
            "Feels personal and attentive.",
            "Example: reminds about a preferred weekly review time.",
        ),
    },
    {
        "id": "operations_manager",
        "name": "Operations Manager",
        "help": _help(
            "Watches workflows, tasks, and operational signals.",
            "Fewer missed follow-ups across departments.",
            "Example: flags overdue approvals.",
        ),
    },
    {
        "id": "business_advisor",
        "name": "Business Advisor",
        "help": _help(
            "Offers thoughtful guidance from organization activity.",
            "Better strategic conversations with less preparation.",
            "Example: suggests focusing on high-margin opportunities.",
        ),
    },
    {
        "id": "ceo_assistant",
        "name": "CEO Assistant",
        "help": _help(
            "Acts as a trusted partner for executive priorities.",
            "Clear leadership visibility across the company.",
            "Example: builds an executive report before the board call.",
        ),
    },
    {
        "id": "custom",
        "name": "Custom",
        "help": _help(
            "Define a Concierge role unique to your organization.",
            "Fits any operating style.",
            "Example: Clinic Concierge for medical practices.",
        ),
    },
]

ORG_ACCESS = [
    {"id": "crm", "name": "CRM", "help": _help("Customer records and pipeline.", "Concierge understands clients and deals.", "Example: checks open opportunities.", "What it is: customer system.")},
    {"id": "erp", "name": "ERP", "help": _help("Core operations and resources.", "Answers reflect how the business runs.", "Example: reviews inventory signals.", "What it is: operations system.")},
    {"id": "documents", "name": "Documents", "help": _help("Company files and folders.", "Finds important papers quickly.", "Example: opens the latest proposal.", "What it is: document library.")},
    {"id": "knowledge", "name": "Knowledge", "help": _help("Approved company knowledge.", "Consistent guidance for everyone.", "Example: uses the refund policy.", "What it is: knowledge base.")},
    {"id": "ai_registry", "name": "AI Registry", "help": _help("Directory of AI Specialists.", "Concierge can find the right expert.", "Example: invites Sales AI to help.", "What it is: specialist registry.")},
    {"id": "workflow_engine", "name": "Workflow Engine", "help": _help("Business process engine.", "Starts and follows work flows.", "Example: launches onboarding.", "What it is: workflow system.")},
    {"id": "analytics", "name": "Analytics", "help": _help("Business metrics and trends.", "Clearer insights for decisions.", "Example: highlights conversion drop.", "What it is: analytics.")},
    {"id": "calendar", "name": "Calendar", "help": _help("Meetings and schedule.", "Reliable planning support.", "Example: prepares tomorrow’s agenda.", "What it is: calendar.")},
    {"id": "tasks", "name": "Tasks", "help": _help("To-dos and assignments.", "Keeps work moving.", "Example: suggests next owner action.", "What it is: task list.")},
    {"id": "marketplace", "name": "Marketplace", "help": _help("Listings and marketplace activity.", "Supports growth opportunities.", "Example: flags a hot listing.", "What it is: marketplace.")},
    {"id": "notifications", "name": "Notifications", "help": _help("Alerts and messages.", "Important news reaches people in time.", "Example: notifies about a deadline.", "What it is: notifications.")},
    {"id": "automation", "name": "Automation", "help": _help("Repeatable automated actions.", "Less manual busywork.", "Example: triggers a welcome sequence.", "What it is: automation.")},
    {"id": "dashboards", "name": "Dashboards", "help": _help("Visual business boards.", "Quick understanding of status.", "Example: opens executive dashboard.", "What it is: dashboards.")},
    {"id": "departments", "name": "Departments", "help": _help("Organization departments and teams.", "Coordinates across the company map.", "Example: routes a request to Finance.", "What it is: department map.")},
]

ORCHESTRATION = [
    {"id": "delegate_tasks", "name": "Delegate tasks", "help": _help("Hands work to the right specialist.", "Owner stays focused.", "Example: asks Legal AI to review a contract.")},
    {"id": "call_specialists", "name": "Call Specialists", "help": _help("Brings specialists into the conversation.", "Faster expert answers.", "Example: invites Finance AI for a cash question.")},
    {"id": "monitor_specialists", "name": "Monitor Specialists", "help": _help("Watches specialist progress.", "Fewer stalled tasks.", "Example: notices a report still pending.")},
    {"id": "coordinate_team", "name": "Coordinate Team", "help": _help("Aligns several specialists as a team.", "Smoother multi-expert work.", "Example: Sales + Marketing joint brief.")},
    {"id": "summarize_discussions", "name": "Summarize Discussions", "help": _help("Turns long chats into clear takeaways.", "Saves reading time.", "Example: summary of a specialist huddle.")},
    {"id": "recommend_specialists", "name": "Recommend Specialists", "help": _help("Suggests who should help next.", "Right expert, faster.", "Example: recommends Construction AI for permits.")},
    {"id": "prepare_meetings", "name": "Prepare Meetings", "help": _help("Builds agendas and prep packs.", "Meetings start ready.", "Example: CEO briefing before standup.")},
    {"id": "create_executive_reports", "name": "Create Executive Reports", "help": _help("Produces leadership-ready reports.", "Better visibility.", "Example: weekly organization digest.")},
]

PROACTIVE = [
    {"id": "morning_briefing", "name": "Morning Briefing", "help": _help("Starts the day with a clear overview.", "Owner begins informed.", "Example: top 3 priorities at 8:00.")},
    {"id": "evening_summary", "name": "Evening Summary", "help": _help("Closes the day with progress notes.", "Easy end-of-day clarity.", "Example: what moved and what waits.")},
    {"id": "important_reminders", "name": "Important Reminders", "help": _help("Surfaces time-sensitive items.", "Fewer missed moments.", "Example: contract renewal reminder.")},
    {"id": "upcoming_meetings", "name": "Upcoming Meetings", "help": _help("Highlights meetings ahead.", "Better preparation.", "Example: agenda for the next call.")},
    {"id": "task_suggestions", "name": "Task Suggestions", "help": _help("Suggests useful next actions.", "Steady momentum.", "Example: follow up with hot leads.")},
    {"id": "business_opportunities", "name": "Business Opportunities", "help": _help("Points to promising openings.", "Growth awareness.", "Example: marketplace demand spike.")},
    {"id": "organization_insights", "name": "Organization Insights", "help": _help("Shares patterns across the company.", "Better situational awareness.", "Example: logistics capacity trend.")},
    {"id": "performance_highlights", "name": "Performance Highlights", "help": _help("Celebrates and surfaces results.", "Motivation and focus.", "Example: record week for Sales.")},
    {"id": "daily_digest", "name": "Daily Digest", "help": _help("One daily package of essentials.", "Less noise, more signal.", "Example: compact noon digest.")},
]

OWNER_RELATIONSHIPS = [
    {"id": "only_when_requested", "name": "Only when requested", "help": _help("Speaks when asked.", "Quiet and respectful.", "Example: waits for owner prompts.")},
    {"id": "balanced", "name": "Balanced", "help": _help("Helpful without overwhelming.", "Comfortable everyday support.", "Example: a few timely nudges.")},
    {"id": "highly_proactive", "name": "Highly Proactive", "help": _help("Actively brings useful updates.", "Owner stays ahead.", "Example: morning and evening outreach.")},
    {"id": "executive_assistant", "name": "Executive Assistant", "help": _help("Protects the owner’s time and priorities.", "Executive-grade support.", "Example: filters noise before it reaches the owner.")},
    {"id": "business_partner", "name": "Business Partner", "help": _help("Thinks with the owner about outcomes.", "Collaborative decisions.", "Example: discusses strategy options.")},
    {"id": "daily_strategic_advisor", "name": "Daily Strategic Advisor", "help": _help("Offers daily strategic perspective.", "Continuous leadership clarity.", "Example: daily focus recommendation.")},
]

RECOMMENDATIONS = [
    {"id": "recommend_specialists", "name": "Recommend Specialists", "architecture_only": True},
    {"id": "recommend_workflows", "name": "Recommend Workflows", "architecture_only": True},
    {"id": "recommend_automations", "name": "Recommend Automations", "architecture_only": True},
    {"id": "recommend_dashboards", "name": "Recommend Dashboards", "architecture_only": True},
    {"id": "recommend_reports", "name": "Recommend Reports", "architecture_only": True},
    {"id": "recommend_knowledge", "name": "Recommend Knowledge", "architecture_only": True},
    {"id": "recommend_vertical_expansion", "name": "Recommend Vertical Expansion", "architecture_only": True},
]

RULES = {
    "one_per_organization": True,
    "independent_from_ai_agents": True,
    "coordinates_specialists": True,
    "specialists_execute_work": True,
}


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "communication_styles": COMMUNICATION_STYLES,
        "voice_profiles": VOICE_PROFILES,
        "avatars": AVATARS,
        "roles": ROLES,
        "organization_access": ORG_ACCESS,
        "orchestration": ORCHESTRATION,
        "proactive": PROACTIVE,
        "owner_relationships": OWNER_RELATIONSHIPS,
        "recommendations": RECOMMENDATIONS,
        "rules": RULES,
        "group_ai_chat": {
            "status": "supported_architecture",
            "description": "Concierge orchestration is ready to coordinate future Group AI Chat sessions.",
        },
    }
