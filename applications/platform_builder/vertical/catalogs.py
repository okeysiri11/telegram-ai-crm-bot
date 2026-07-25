"""Vertical Builder catalogs — Sprint 28.4."""

from __future__ import annotations

from typing import Any


def _help(purpose: str, benefits: str, example: str, what: str = "", use_cases: str = "") -> dict[str, str]:
    return {
        "short_description": what or purpose,
        "purpose": purpose,
        "description": purpose,
        "benefits": benefits,
        "business_benefits": benefits,
        "business_value": benefits,
        "example": example,
        "typical_use_cases": use_cases or example,
        "tooltip": purpose,
        "more_information": f"{purpose} {benefits}",
    }


WIZARD_STEPS = [
    {"id": "information", "title": "Vertical Information", "index": 1},
    {"id": "industry", "title": "Select Industry", "index": 2},
    {"id": "modules", "title": "Module Selection", "index": 3},
    {"id": "ai_configuration", "title": "AI Configuration", "index": 4},
    {"id": "concierge", "title": "AI Concierge", "index": 5},
    {"id": "dashboard", "title": "Dashboard", "index": 6},
    {"id": "workspace", "title": "Workspace", "index": 7},
    {"id": "organization_preview", "title": "Live Organization Preview", "index": 8},
    {"id": "summary", "title": "Summary", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

BUSINESS_SIZES = (
    {"id": "solo", "name": "Solo"},
    {"id": "small", "name": "Small"},
    {"id": "medium", "name": "Medium"},
    {"id": "enterprise", "name": "Enterprise"},
)

BRAND_COLORS = (
    {"id": "ocean", "name": "Ocean", "hex": "#1B6CA8"},
    {"id": "forest", "name": "Forest", "hex": "#2F6B4F"},
    {"id": "ember", "name": "Ember", "hex": "#C45C26"},
    {"id": "slate", "name": "Slate", "hex": "#4A5568"},
    {"id": "violet", "name": "Violet", "hex": "#5B4B8A"},
)

INDUSTRIES = [
    {
        "id": "medical",
        "name": "Medical",
        "help": _help(
            "Healthcare clinics and medical practices.",
            "Faster patient coordination and clearer operational visibility.",
            "Example: dental clinic with visit CRM and Medical AI.",
            "What it is: medical vertical",
            "Patient intake, treatment plans, follow-ups.",
        ),
    },
    {
        "id": "beauty",
        "name": "Beauty",
        "help": _help(
            "Salons, spas, and beauty studios.",
            "Better booking rhythm and client retention.",
            "Example: salon with appointment CRM.",
            "What it is: beauty vertical",
            "Appointments, memberships, product sales.",
        ),
    },
    {
        "id": "construction",
        "name": "Construction",
        "help": _help(
            "Builders and project contractors.",
            "Clearer project tracking and document control.",
            "Example: renovation firm with project ERP.",
            "What it is: construction vertical",
            "Sites, permits, materials, crews.",
        ),
    },
    {
        "id": "manufacturing",
        "name": "Manufacturing",
        "help": _help(
            "Production and factory operations.",
            "Tighter inventory and production awareness.",
            "Example: parts plant with warehouse + ERP.",
            "What it is: manufacturing vertical",
            "BOMs, production runs, quality checks.",
        ),
    },
    {
        "id": "automotive",
        "name": "Automotive",
        "help": _help(
            "Dealerships, service, and auto marketplace.",
            "Stronger inventory and customer lifecycle.",
            "Example: dealer with vehicle CRM.",
            "What it is: automotive vertical",
            "Sales pipeline, service bookings, parts.",
        ),
    },
    {
        "id": "agriculture",
        "name": "Agriculture",
        "help": _help(
            "Farms and agribusiness operations.",
            "Seasonal planning with clearer field insights.",
            "Example: farm with crop analytics.",
            "What it is: agriculture vertical",
            "Fields, harvest, suppliers, logistics.",
        ),
    },
    {
        "id": "education",
        "name": "Education",
        "help": _help(
            "Schools, academies, and training centers.",
            "Smoother enrollment and learning operations.",
            "Example: academy with student CRM.",
            "What it is: education vertical",
            "Enrollment, classes, tutors, billing.",
        ),
    },
    {
        "id": "retail",
        "name": "Retail",
        "help": _help(
            "Stores and omnichannel retail.",
            "Better stock visibility and customer journeys.",
            "Example: boutique with marketplace + CRM.",
            "What it is: retail vertical",
            "Catalog, orders, loyalty, returns.",
        ),
    },
    {
        "id": "finance",
        "name": "Finance",
        "help": _help(
            "Financial services and advisory firms.",
            "Clearer client portfolios and compliance rhythm.",
            "Example: advisory desk with Finance AI.",
            "What it is: finance vertical",
            "Clients, portfolios, reports, reminders.",
        ),
    },
    {
        "id": "legal",
        "name": "Legal",
        "help": _help(
            "Law firms and legal practices.",
            "Faster matter tracking and document readiness.",
            "Example: firm with Legal AI and knowledge base.",
            "What it is: legal vertical",
            "Matters, contracts, deadlines, clients.",
        ),
    },
    {
        "id": "crypto",
        "name": "Crypto",
        "help": _help(
            "Digital asset and crypto operations.",
            "Faster market awareness with specialist AI.",
            "Example: trading desk with Crypto AI.",
            "What it is: crypto vertical",
            "Watchlists, alerts, treasury, reporting.",
        ),
    },
    {
        "id": "hospitality",
        "name": "Hospitality",
        "help": _help(
            "Hotels and guest experience businesses.",
            "Smoother bookings and guest concierge support.",
            "Example: boutique hotel with Concierge + CRM.",
            "What it is: hospitality vertical",
            "Reservations, rooms, guests, upsells.",
        ),
    },
    {
        "id": "logistics",
        "name": "Logistics",
        "help": _help(
            "Freight, fleet, and delivery networks.",
            "Clearer routing and warehouse coordination.",
            "Example: courier with logistics ERP.",
            "What it is: logistics vertical",
            "Shipments, routes, warehouses, partners.",
        ),
    },
    {
        "id": "real_estate",
        "name": "Real Estate",
        "help": _help(
            "Agencies and property operations.",
            "Faster listings and client matching.",
            "Example: agency with listing CRM.",
            "What it is: real estate vertical",
            "Listings, viewings, contracts, owners.",
        ),
    },
    {
        "id": "port",
        "name": "Port",
        "help": _help(
            "Port and terminal operations.",
            "Better berth and cargo coordination.",
            "Example: terminal with Port Director AI.",
            "What it is: port vertical",
            "Berths, cargo, vessels, customs.",
        ),
    },
    {
        "id": "marketplace",
        "name": "Marketplace",
        "help": _help(
            "Multi-vendor marketplace platforms.",
            "Stronger seller and listing operations.",
            "Example: auto marketplace with seller CRM.",
            "What it is: marketplace vertical",
            "Listings, vendors, orders, payouts.",
        ),
    },
    {
        "id": "restaurant",
        "name": "Restaurant",
        "help": _help(
            "Restaurants and food service.",
            "Smoother reservations and kitchen ops.",
            "Example: restaurant with booking CRM.",
            "What it is: restaurant vertical",
            "Menus, tables, orders, suppliers.",
        ),
    },
    {
        "id": "custom",
        "name": "Custom",
        "help": _help(
            "Define a vertical unique to your organization.",
            "Fits any industry blueprint.",
            "Example: niche clinic network.",
            "What it is: custom vertical",
            "Any modules and AI mix you choose.",
        ),
    },
]

MODULES = [
    {"id": "crm", "name": "CRM", "help": _help("Customer and pipeline management.", "Stronger relationships and follow-ups.", "Example: track clinic patients.")},
    {"id": "erp", "name": "ERP", "help": _help("Core business operations.", "One operational backbone.", "Example: manage production resources.")},
    {"id": "finance", "name": "Finance", "help": _help("Money, invoices, and cash flow.", "Clearer financial control.", "Example: weekly cash overview.")},
    {"id": "warehouse", "name": "Warehouse", "help": _help("Inventory and stock locations.", "Fewer stock surprises.", "Example: parts warehouse levels.")},
    {"id": "documents", "name": "Documents", "help": _help("Files and document folders.", "Faster document access.", "Example: contracts library.")},
    {"id": "analytics", "name": "Analytics", "help": _help("Metrics and business trends.", "Better decision visibility.", "Example: conversion dashboard.")},
    {"id": "knowledge_base", "name": "Knowledge Base", "help": _help("Approved company knowledge.", "Consistent answers for teams and AI.", "Example: refund policy wiki.")},
    {"id": "automation", "name": "Automation", "help": _help("Repeatable automated actions.", "Less manual busywork.", "Example: welcome sequence.")},
    {"id": "marketplace", "name": "Marketplace", "help": _help("Listings and marketplace ops.", "Growth through selling channels.", "Example: published listings board.")},
    {"id": "telegram", "name": "Telegram", "help": _help("Telegram messaging channel.", "Reach customers where they chat.", "Example: booking bot.")},
    {"id": "mobile", "name": "Mobile", "help": _help("Mobile experience layer.", "Work on the go.", "Example: field staff app.")},
    {"id": "website", "name": "Website", "help": _help("Public web presence.", "Attract and convert visitors.", "Example: booking landing page.")},
    {"id": "api", "name": "API", "help": _help("Integration endpoints.", "Connect external systems.", "Example: partner sync API.")},
    {"id": "calendar", "name": "Calendar", "help": _help("Schedules and meetings.", "Reliable planning.", "Example: clinic appointment calendar.")},
    {"id": "notifications", "name": "Notifications", "help": _help("Alerts and reminders.", "Important news arrives on time.", "Example: renewal reminder.")},
    {"id": "workflows", "name": "Workflows", "help": _help("Business process flows.", "Consistent handoffs.", "Example: onboarding workflow.")},
]

AI_MODES = [
    {
        "id": "connect_existing",
        "name": "Connect existing AI Team",
        "help": _help(
            "Link specialists already in AI Team Center / AI Registry.",
            "Reuse trained specialists immediately.",
            "Example: attach Medical + Finance AI to a clinic vertical.",
        ),
    },
    {
        "id": "launch_ai_builder",
        "name": "Launch AI Builder",
        "help": _help(
            "Open AI Builder to create new specialists for this vertical.",
            "Build the exact AI team your industry needs.",
            "Example: create Construction AI with permit knowledge.",
        ),
    },
]

CONCIERGE_MODES = [
    {
        "id": "attach_existing",
        "name": "Attach Concierge",
        "help": _help(
            "Attach the organization’s existing Concierge.",
            "Keep one central intelligence linked to the vertical.",
            "Example: attach Nova Concierge to Medical Vertical.",
        ),
    },
    {
        "id": "create_new",
        "name": "Create New Concierge",
        "help": _help(
            "Prepare a new Concierge via Concierge Builder.",
            "Stand up executive assistance with the vertical.",
            "Example: launch Concierge Builder for a new org.",
        ),
    },
]

DASHBOARD_WIDGETS = [
    {"id": "kpi_overview", "name": "KPI Overview"},
    {"id": "pipeline", "name": "Pipeline"},
    {"id": "revenue", "name": "Revenue"},
    {"id": "ai_team_status", "name": "AI Team Status"},
    {"id": "concierge_brief", "name": "Concierge Brief"},
    {"id": "tasks", "name": "Tasks"},
    {"id": "calendar", "name": "Calendar"},
    {"id": "alerts", "name": "Alerts"},
    {"id": "knowledge_highlights", "name": "Knowledge Highlights"},
    {"id": "organization_map", "name": "Organization Map"},
]

DEFAULT_DEPARTMENTS = (
    "Leadership",
    "Operations",
    "Sales",
    "Finance",
    "Support",
)

AI_EXPLANATION = (
    "Every AI Specialist has independent memory and specialization. "
    "Multiple AI Specialists work together as one intelligent organization."
)

VISUAL_CONSUMERS = (
    "AI Operations Center",
    "AI Team Center",
    "2D AI City",
    "Future 3D Visualization",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "business_sizes": list(BUSINESS_SIZES),
        "brand_colors": list(BRAND_COLORS),
        "industries": INDUSTRIES,
        "modules": MODULES,
        "ai_modes": AI_MODES,
        "concierge_modes": CONCIERGE_MODES,
        "dashboard_widgets": DASHBOARD_WIDGETS,
        "default_departments": list(DEFAULT_DEPARTMENTS),
        "ai_explanation": AI_EXPLANATION,
        "visual_consumers": list(VISUAL_CONSUMERS),
        "architecture_rule": {
            "logical_representation": True,
            "visual_representation": True,
            "platform_registry": True,
        },
    }
