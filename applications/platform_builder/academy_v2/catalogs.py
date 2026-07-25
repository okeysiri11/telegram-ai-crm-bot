"""Builder Academy 2.0 catalogs — Sprint 28.6."""

from __future__ import annotations

from typing import Any


EXPERIENCE_LEVELS = (
    {
        "id": "beginner",
        "name": "Beginner",
        "description": "Full explanations, walkthroughs, and protective defaults.",
        "adaptations": {
            "show_tips": True,
            "show_walkthrough": True,
            "show_best_practices": True,
            "show_common_mistakes": True,
            "compact_ui": False,
            "auto_recommend": True,
        },
    },
    {
        "id": "intermediate",
        "name": "Intermediate",
        "description": "Balanced guidance with examples and recommendations.",
        "adaptations": {
            "show_tips": True,
            "show_walkthrough": False,
            "show_best_practices": True,
            "show_common_mistakes": True,
            "compact_ui": False,
            "auto_recommend": True,
        },
    },
    {
        "id": "advanced",
        "name": "Advanced",
        "description": "Concise tips with optional deep dives.",
        "adaptations": {
            "show_tips": True,
            "show_walkthrough": False,
            "show_best_practices": False,
            "show_common_mistakes": False,
            "compact_ui": True,
            "auto_recommend": True,
        },
    },
    {
        "id": "expert",
        "name": "Expert",
        "description": "Minimal chrome — guidance on demand only.",
        "adaptations": {
            "show_tips": False,
            "show_walkthrough": False,
            "show_best_practices": False,
            "show_common_mistakes": False,
            "compact_ui": True,
            "auto_recommend": False,
        },
    },
)

WIZARD_STEPS = [
    {"id": "experience", "title": "User Experience Level", "index": 1},
    {"id": "contextual_help", "title": "Contextual Help", "index": 2},
    {"id": "ai_guide", "title": "AI Guide", "index": 3},
    {"id": "recommendations", "title": "Smart Recommendations", "index": 4},
    {"id": "interactive_learning", "title": "Interactive Learning", "index": 5},
    {"id": "live_analysis", "title": "Live Builder Analysis", "index": 6},
    {"id": "business_impact", "title": "Business Impact", "index": 7},
    {"id": "progress", "title": "Academy Progress", "index": 8},
    {"id": "summary", "title": "Summary", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

HELP_FIELDS = (
    "explanation",
    "business_purpose",
    "example",
    "best_practice",
    "common_mistakes",
    "more_information",
)

AI_GUIDE_FUNCTIONS = (
    "Explain current step",
    "Recommend configuration",
    "Answer Builder questions",
    "Suggest improvements",
    "Warn about missing components",
)

RECOMMENDATION_TYPES = (
    {"id": "ai_specialists", "name": "AI Specialists"},
    {"id": "modules", "name": "Modules"},
    {"id": "departments", "name": "Departments"},
    {"id": "dashboards", "name": "Dashboards"},
    {"id": "automations", "name": "Automations"},
    {"id": "marketplace_apps", "name": "Marketplace Apps"},
    {"id": "knowledge_sources", "name": "Knowledge Sources"},
)

LEARNING_ELEMENTS = (
    "Tips",
    "Walkthroughs",
    "Progress",
    "Achievements",
    "Learning Path",
)

ANALYSIS_DIMENSIONS = (
    "Strengths",
    "Missing Components",
    "Optimization Ideas",
    "Future Recommendations",
)

IMPACT_FIELDS = (
    "Business Value",
    "Expected Benefits",
    "Typical Industry Usage",
    "Estimated Impact",
)

ACHIEVEMENTS = (
    {"id": "first_builder", "name": "First Builder", "description": "Created your first builder object."},
    {"id": "guided_learner", "name": "Guided Learner", "description": "Completed a full Academy walkthrough."},
    {"id": "ai_coach_user", "name": "AI Coach User", "description": "Asked the AI Guide a question."},
    {"id": "optimizer", "name": "Optimizer", "description": "Applied a live analysis recommendation."},
    {"id": "business_ready", "name": "Business Ready", "description": "Reached business readiness score ≥ 80."},
)

LEARNING_PATH = (
    {"id": "intro", "title": "Meet the Builders", "lesson": "Understand Platform Builder modules."},
    {"id": "help", "title": "Use Contextual Help", "lesson": "Read Purpose, Example, Best Practice on every field."},
    {"id": "guide", "title": "Talk to AI Guide", "lesson": "Ask for step explanations and improvements."},
    {"id": "recommend", "title": "Apply Recommendations", "lesson": "Accept smart specialist and module suggestions."},
    {"id": "analyze", "title": "Run Live Analysis", "lesson": "Fix missing components before create."},
    {"id": "impact", "title": "Measure Business Impact", "lesson": "Review value of each selected option."},
)


def contextual_help_for(field: str, builder_id: str = "generic") -> dict[str, str]:
    label = field.replace("_", " ")
    return {
        "field": field,
        "explanation": f"«{label}» defines how this part of {builder_id} behaves.",
        "business_purpose": f"Choosing the right {label} keeps operations clear and consistent.",
        "example": f"Example: configure {label} to match your team’s daily rhythm.",
        "best_practice": f"Start simple, then refine {label} after the first successful create.",
        "common_mistakes": f"Skipping {label} or over-configuring it before the first preview.",
        "more_information": f"Academy 2.0 expands {label} with tips, impact, and live recommendations.",
    }


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "experience_levels": list(EXPERIENCE_LEVELS),
        "help_fields": list(HELP_FIELDS),
        "ai_guide_functions": list(AI_GUIDE_FUNCTIONS),
        "recommendation_types": list(RECOMMENDATION_TYPES),
        "learning_elements": list(LEARNING_ELEMENTS),
        "analysis_dimensions": list(ANALYSIS_DIMENSIONS),
        "impact_fields": list(IMPACT_FIELDS),
        "achievements": list(ACHIEVEMENTS),
        "learning_path": list(LEARNING_PATH),
    }
