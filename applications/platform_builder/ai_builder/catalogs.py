"""AI Builder catalogs — plain-language options for the wizard."""

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


AGENT_COUNTS = [
    {"value": 1, "label": "1", "help": _help(
        "One focused specialist for a clear job.",
        "Simple to manage when you need a single expert.",
        "Example: one Sales AI that greets every new lead.",
        "Create a single AI specialist.",
    )},
    {"value": 2, "label": "2", "help": _help("Two specialists that cover related work.", "They can hand work to each other.", "Example: Sales AI + Finance AI.", "A small AI pair.")},
    {"value": 3, "label": "3", "help": _help("A compact team of three.", "Good balance of coverage and simplicity.", "Example: Sales, Marketing, and Support.", "Three AI teammates.")},
    {"value": 5, "label": "5", "help": _help("A full working team.", "Covers most daily business roles.", "Example: Sales, Law, Accounting, Marketing, Support.", "Five specialists.")},
    {"value": 10, "label": "10", "help": _help("A large department of AI specialists.", "Ideal for growing organizations.", "Example: one AI for each major business area.", "Ten specialists.")},
    {"value": 20, "label": "20", "help": _help("An enterprise-scale AI workforce.", "Strong coverage across the company.", "Example: specialists for every vertical and department.", "Twenty specialists.")},
    {"value": "custom", "label": "Custom", "help": _help("Choose any team size you need.", "Full flexibility for unique setups.", "Example: create exactly 7 specialists.", "Pick your own number.")},
]

WHY_MULTI_AGENT = {
    "title": "Why use multiple AI agents?",
    "summary": (
        "Every AI agent is an independent specialist with its own memory, experience, and role. "
        "Several specialists work as one intelligent team instead of one overloaded assistant."
    ),
    "points": [
        "Each specialist remembers what matters for their job.",
        "Work is shared across the team instead of piled onto one helper.",
        "You can invite the right expert into a conversation when needed.",
    ],
    "illustration": {
        "kind": "ai_team",
        "members": ["Sales AI", "Finance AI", "Legal AI", "Support AI"],
        "caption": "An AI Team — independent specialists working together",
    },
}

NAME_SUGGESTIONS = {
    "male": ["Alex", "Jordan", "Marcus", "Noah", "Leo", "Daniel"],
    "female": ["Ava", "Sofia", "Mia", "Elena", "Nora", "Clara"],
    "neutral": ["River", "Quinn", "Sage", "Blair", "Casey", "Taylor"],
}

PROFESSIONS = [
    {"id": "sales", "name": "Sales", "help": _help("Helps win customers and close deals.", "Faster replies and clearer follow-ups.", "Example: qualifies new marketplace leads.")},
    {"id": "marketing", "name": "Marketing", "help": _help("Shapes messages and campaigns.", "Keeps brand voice consistent.", "Example: drafts weekly social posts.")},
    {"id": "law", "name": "Law", "help": _help("Supports legal review and contracts.", "Reduces waiting on routine documents.", "Example: prepares a service agreement draft.")},
    {"id": "accounting", "name": "Accounting", "help": _help("Tracks numbers and bookkeeping tasks.", "Cleaner financial records.", "Example: summarizes monthly invoices.")},
    {"id": "finance", "name": "Finance", "help": _help("Looks after money, forecasts, and budgets.", "Better spending visibility.", "Example: checks cash runway.")},
    {"id": "medical", "name": "Medical", "help": _help("Supports healthcare operations.", "Clearer patient and clinic workflows.", "Example: prepares visit summaries.")},
    {"id": "construction", "name": "Construction", "help": _help("Supports building projects and sites.", "Fewer missed site details.", "Example: tracks permit checklists.")},
    {"id": "beauty", "name": "Beauty", "help": _help("Supports salons and beauty studios.", "Smoother bookings and client care.", "Example: suggests rebooking times.")},
    {"id": "manufacturing", "name": "Manufacturing", "help": _help("Supports production floors.", "Faster operational answers.", "Example: explains a production delay.")},
    {"id": "education", "name": "Education", "help": _help("Supports learning and training.", "Clearer lessons and onboarding.", "Example: builds a short study plan.")},
    {"id": "retail", "name": "Retail", "help": _help("Supports stores and product sales.", "Better product answers for shoppers.", "Example: recommends matching items.")},
    {"id": "hospitality", "name": "Hospitality", "help": _help("Supports hotels and guest services.", "Warmer guest experiences.", "Example: prepares welcome notes.")},
    {"id": "real_estate", "name": "Real Estate", "help": _help("Supports property sales and rentals.", "Faster listing and viewing help.", "Example: summarizes a property brief.")},
    {"id": "crypto", "name": "Crypto", "help": _help("Supports digital asset operations.", "Clearer market and treasury answers.", "Example: explains a wallet activity summary.")},
    {"id": "agriculture", "name": "Agriculture", "help": _help("Supports farms and field operations.", "Better seasonal planning help.", "Example: reviews crop checklist notes.")},
    {"id": "custom", "name": "Custom", "help": _help("Define any profession you need.", "Fits unique businesses.", "Example: Fleet Operations Specialist.")},
]

SPECIALIZATION_TREE: dict[str, list[dict[str, Any]]] = {
    "medical": [
        {
            "id": "dentistry",
            "name": "Dentistry",
            "children": [
                {"id": "implantology", "name": "Implantology"},
                {"id": "orthodontics", "name": "Orthodontics"},
                {"id": "therapy", "name": "Therapy"},
                {"id": "surgery", "name": "Surgery"},
            ],
        },
        {
            "id": "general_practice",
            "name": "General Practice",
            "children": [
                {"id": "family_medicine", "name": "Family Medicine"},
                {"id": "preventive_care", "name": "Preventive Care"},
            ],
        },
    ],
    "law": [
        {
            "id": "corporate",
            "name": "Corporate",
            "children": [
                {"id": "contracts", "name": "Contracts"},
                {"id": "compliance", "name": "Compliance"},
            ],
        },
        {
            "id": "litigation",
            "name": "Litigation",
            "children": [
                {"id": "civil", "name": "Civil"},
                {"id": "commercial", "name": "Commercial"},
            ],
        },
    ],
    "sales": [
        {
            "id": "outbound",
            "name": "Outbound",
            "children": [
                {"id": "lead_qualification", "name": "Lead Qualification"},
                {"id": "demo_follow_up", "name": "Demo Follow-up"},
            ],
        },
        {
            "id": "account",
            "name": "Account Management",
            "children": [
                {"id": "upsell", "name": "Upsell"},
                {"id": "retention", "name": "Retention"},
            ],
        },
    ],
    "finance": [
        {
            "id": "treasury",
            "name": "Treasury",
            "children": [
                {"id": "cash_flow", "name": "Cash Flow"},
                {"id": "forecasting", "name": "Forecasting"},
            ],
        }
    ],
    "beauty": [
        {
            "id": "salon",
            "name": "Salon Operations",
            "children": [
                {"id": "booking", "name": "Booking"},
                {"id": "client_care", "name": "Client Care"},
            ],
        }
    ],
    "construction": [
        {
            "id": "site",
            "name": "Site Operations",
            "children": [
                {"id": "permits", "name": "Permits"},
                {"id": "safety", "name": "Safety"},
            ],
        }
    ],
    "default": [
        {
            "id": "general",
            "name": "General",
            "children": [
                {"id": "operations", "name": "Operations"},
                {"id": "advisory", "name": "Advisory"},
            ],
        }
    ],
}

KNOWLEDGE_SOURCES = [
    {"id": "crm", "name": "CRM", "help": _help("Customer records and conversations.", "AI answers with real client context.", "Example: recalls the latest deal stage.", "What it is: your customer database.")},
    {"id": "erp", "name": "ERP", "help": _help("Company operations and inventory systems.", "Answers reflect how the business runs day to day.", "Example: checks stock availability.", "What it is: core business systems.")},
    {"id": "documents", "name": "Documents", "help": _help("Shared files and folders.", "Finds answers inside company files.", "Example: opens the onboarding pack.", "What it is: your document library.")},
    {"id": "pdf", "name": "PDF", "help": _help("PDF files such as manuals and contracts.", "Reads locked-in documents safely.", "Example: summarizes a policy PDF.", "What it is: portable document files.")},
    {"id": "word", "name": "Word", "help": _help("Word documents and drafts.", "Helps with written procedures and letters.", "Example: rewrites a client letter.", "What it is: editable text documents.")},
    {"id": "excel", "name": "Excel", "help": _help("Spreadsheets and tables.", "Works with numbers and lists.", "Example: explains a pricing sheet.", "What it is: spreadsheet data.")},
    {"id": "knowledge_base", "name": "Knowledge Base", "help": _help("Approved company answers and playbooks.", "Keeps replies consistent.", "Example: uses the refund policy article.", "What it is: curated Q&A knowledge.")},
    {"id": "email", "name": "Email", "help": _help("Business email threads.", "Understands recent conversations.", "Example: drafts a reply to a supplier.", "What it is: your mailbox context.")},
    {"id": "calendar", "name": "Calendar", "help": _help("Meetings and schedules.", "Plans around real availability.", "Example: finds an open slot tomorrow.", "What it is: your schedule.")},
    {"id": "telegram", "name": "Telegram", "help": _help("Telegram chats and bots.", "Helps where your team already talks.", "Example: answers a channel question.", "What it is: Telegram messaging.")},
    {"id": "marketplace", "name": "Marketplace", "help": _help("Listings, offers, and marketplace activity.", "Supports selling and buying flows.", "Example: reviews a new listing draft.", "What it is: marketplace data.")},
    {"id": "custom", "name": "Custom Sources", "help": _help("Any other source you connect later.", "Fits unique tools.", "Example: a proprietary catalog API.", "What it is: your custom data source.")},
]

SKILLS = [
    {"id": "answer_questions", "name": "Answer Questions", "help": _help("Replies to people in clear language.", "Faster everyday support.", "Example: answers «What is our refund window?»")},
    {"id": "analyze_documents", "name": "Analyze Documents", "help": _help("Reads and explains files.", "Saves hours of manual reading.", "Example: highlights key clauses in a contract.")},
    {"id": "create_reports", "name": "Create Reports", "help": _help("Builds summaries and reports.", "Ready-to-share updates.", "Example: weekly sales snapshot.")},
    {"id": "create_contracts", "name": "Create Contracts", "help": _help("Prepares contract drafts.", "Speeds legal paperwork starts.", "Example: service agreement template fill.")},
    {"id": "calendar", "name": "Calendar", "help": _help("Works with meetings and reminders.", "Fewer scheduling mistakes.", "Example: books a follow-up call.")},
    {"id": "crm_operations", "name": "CRM Operations", "help": _help("Updates and uses CRM records.", "Keeps customer data fresh.", "Example: logs a call outcome.")},
    {"id": "workflow", "name": "Workflow", "help": _help("Starts and follows business workflows.", "Work moves without waiting.", "Example: launches onboarding flow.")},
    {"id": "automation", "name": "Automation", "help": _help("Triggers repeatable actions.", "Less repetitive clicking.", "Example: auto-sends a welcome pack.")},
    {"id": "analytics", "name": "Analytics", "help": _help("Finds patterns in numbers and activity.", "Clearer decisions.", "Example: spots a drop in conversions.")},
    {"id": "recommendations", "name": "Recommendations", "help": _help("Suggests next best actions.", "Guidance without guesswork.", "Example: recommends which lead to call first.")},
    {"id": "learning", "name": "Learning", "help": _help("Improves from feedback over time.", "Gets more useful with use.", "Example: remembers preferred report format.")},
    {"id": "custom", "name": "Custom", "help": _help("Add a unique ability.", "Fits special processes.", "Example: «Generate packing slips».")},
]

PERMISSIONS = [
    {"id": "read_crm", "name": "Read CRM", "help": _help("Look at customer records.", "Informed answers.", "Example: view a contact card.")},
    {"id": "create_records", "name": "Create Records", "help": _help("Add new records.", "Captures new information quickly.", "Example: create a lead.")},
    {"id": "update_records", "name": "Update Records", "help": _help("Change existing records.", "Keeps data accurate.", "Example: update deal stage.")},
    {"id": "delete_records", "name": "Delete Records", "help": _help("Remove records when allowed.", "Cleans outdated entries.", "Example: archive a duplicate contact.")},
    {"id": "read_knowledge", "name": "Read Knowledge", "help": _help("Use the knowledge base.", "Consistent answers.", "Example: open a policy article.")},
    {"id": "launch_workflow", "name": "Launch Workflow", "help": _help("Start approved workflows.", "Moves work forward.", "Example: start invoice approval.")},
    {"id": "send_notifications", "name": "Send Notifications", "help": _help("Notify people.", "Keeps teams informed.", "Example: ping sales about a hot lead.")},
    {"id": "access_calendar", "name": "Access Calendar", "help": _help("See and use calendar data.", "Reliable scheduling.", "Example: check free slots.")},
    {"id": "access_documents", "name": "Access Documents", "help": _help("Open document libraries.", "Answers from real files.", "Example: open a proposal draft.")},
    {"id": "access_email", "name": "Access Email", "help": _help("Use email context.", "Better conversation continuity.", "Example: draft a reply.")},
]

PERSONALITY = {
    "genders": [
        {"id": "male", "name": "Male"},
        {"id": "female", "name": "Female"},
        {"id": "neutral", "name": "Neutral"},
    ],
    "communication_styles": [
        {"id": "business_professional", "name": "Business Professional", "help": _help("Polished workplace language.", "Trusted in formal settings.", "Example: «Happy to prepare the summary for the board.»")},
        {"id": "expert", "name": "Expert", "help": _help("Confident specialist voice.", "Signals deep knowledge.", "Example: «Based on the clinical checklist…»")},
        {"id": "friendly", "name": "Friendly", "help": _help("Warm and approachable.", "Easy for everyday chats.", "Example: «Glad you asked — here’s a simple answer.»")},
        {"id": "best_friend", "name": "Best Friend", "help": _help("Supportive and close.", "Feels personal and caring.", "Example: «I’ve got you — let’s sort this together.»")},
        {"id": "best_girlfriend", "name": "Best Girlfriend", "help": _help("Affectionate and attentive companion tone.", "Highly personal engagement.", "Example: «Tell me what’s on your mind — I’m right here.»")},
        {"id": "mentor", "name": "Mentor", "help": _help("Guides and teaches.", "Builds confidence.", "Example: «Let’s walk through this one step at a time.»")},
        {"id": "energetic", "name": "Energetic", "help": _help("Upbeat and motivating.", "Adds momentum.", "Example: «Great timing — let’s move!»")},
        {"id": "direct", "name": "Direct", "help": _help("Straight to the point.", "Saves time.", "Example: «Do this next: confirm the budget.»")},
        {"id": "without_formalities", "name": "Without Formalities", "help": _help("Relaxed and simple.", "Removes stiff language.", "Example: «Sure — here’s the short version.»")},
        {"id": "very_informal", "name": "Very Informal", "help": _help("Casual everyday talk.", "Feels like a chat with a peer.", "Example: «Yep, easy — try this.»")},
        {"id": "technical", "name": "Technical", "help": _help("Precise and detailed wording.", "Useful for specialists.", "Example: «Map field X to workflow step 3.»")},
        {"id": "short", "name": "Short", "help": _help("Brief replies.", "Fast scanning.", "Example: «Done. Next?»")},
        {"id": "detailed", "name": "Detailed", "help": _help("Thorough explanations.", "Great for learning.", "Example: a step-by-step walkthrough.")},
    ],
    "professional_tones": [
        {"id": "formal", "name": "Formal"},
        {"id": "balanced", "name": "Balanced"},
        {"id": "casual", "name": "Casual"},
    ],
    "conversation_styles": [
        {"id": "ask_clarify", "name": "Ask clarifying questions"},
        {"id": "offer_options", "name": "Offer options"},
        {"id": "lead_with_action", "name": "Lead with next action"},
    ],
}

WIZARD_STEPS = [
    {"id": "count", "title": "Number of AI Agents", "index": 1},
    {"id": "names", "title": "AI Agent Name", "index": 2},
    {"id": "profession", "title": "Profession", "index": 3},
    {"id": "specialization", "title": "Specialization", "index": 4},
    {"id": "knowledge", "title": "Knowledge", "index": 5},
    {"id": "skills", "title": "Skills", "index": 6},
    {"id": "permissions", "title": "Permissions", "index": 7},
    {"id": "personality", "title": "Personality", "index": 8},
    {"id": "summary", "title": "Summary", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]


def specialization_for(profession_id: str) -> list[dict[str, Any]]:
    return list(SPECIALIZATION_TREE.get(profession_id) or SPECIALIZATION_TREE["default"])


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "agent_counts": AGENT_COUNTS,
        "why_multi_agent": WHY_MULTI_AGENT,
        "name_suggestions": NAME_SUGGESTIONS,
        "professions": PROFESSIONS,
        "specialization_tree": SPECIALIZATION_TREE,
        "knowledge_sources": KNOWLEDGE_SOURCES,
        "skills": SKILLS,
        "permissions": PERMISSIONS,
        "personality": PERSONALITY,
        "group_ai_chat": {
            "status": "foundation",
            "description": "Later, people can invite several AI specialists into one shared conversation.",
            "architecture": {
                "conversation_id": "string",
                "participant_agent_ids": ["agent_id"],
                "moderator": "optional human or orchestrator",
                "turn_policy": "round_robin | capability_routing",
            },
        },
    }
