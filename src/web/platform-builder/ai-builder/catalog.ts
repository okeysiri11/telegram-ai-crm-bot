export type HelpBits = {
  shortDescription: string;
  purpose: string;
  benefits: string;
  example: string;
  businessValue: string;
  tooltip: string;
  moreInformation: string;
};

function help(purpose: string, benefits: string, example: string, what = ""): HelpBits {
  return {
    shortDescription: what || purpose,
    purpose,
    benefits,
    example,
    businessValue: benefits,
    tooltip: purpose,
    moreInformation: `${purpose} ${benefits}`,
  };
}

export const AI_WIZARD_STEPS = [
  "Number of AI Agents",
  "AI Agent Name",
  "Profession",
  "Specialization",
  "Knowledge",
  "Skills",
  "Permissions",
  "Personality",
  "Summary",
  "Create",
] as const;

export const AGENT_COUNTS: { value: number | "custom"; label: string }[] = [
  { value: 1, label: "1" },
  { value: 2, label: "2" },
  { value: 3, label: "3" },
  { value: 5, label: "5" },
  { value: 10, label: "10" },
  { value: 20, label: "20" },
  { value: "custom", label: "Custom" },
];

export const WHY_MULTI = {
  title: "Why use multiple AI agents?",
  summary:
    "Every AI agent is an independent specialist with its own memory, experience, and role. Several specialists work as one intelligent team instead of one overloaded assistant.",
  points: [
    "Each specialist remembers what matters for their job.",
    "Work is shared across the team instead of piled onto one helper.",
    "You can invite the right expert into a conversation when needed.",
  ],
  members: ["Sales AI", "Finance AI", "Legal AI", "Support AI"],
};

export const NAME_SUGGESTIONS = {
  male: ["Alex", "Jordan", "Marcus", "Noah", "Leo", "Daniel"],
  female: ["Ava", "Sofia", "Mia", "Elena", "Nora", "Clara"],
  neutral: ["River", "Quinn", "Sage", "Blair", "Casey", "Taylor"],
};

export const PROFESSIONS = [
  { id: "sales", name: "Sales", help: help("Helps win customers and close deals.", "Faster replies and clearer follow-ups.", "Example: qualifies new marketplace leads.") },
  { id: "marketing", name: "Marketing", help: help("Shapes messages and campaigns.", "Keeps brand voice consistent.", "Example: drafts weekly social posts.") },
  { id: "law", name: "Law", help: help("Supports legal review and contracts.", "Reduces waiting on routine documents.", "Example: prepares a service agreement draft.") },
  { id: "accounting", name: "Accounting", help: help("Tracks numbers and bookkeeping tasks.", "Cleaner financial records.", "Example: summarizes monthly invoices.") },
  { id: "finance", name: "Finance", help: help("Looks after money, forecasts, and budgets.", "Better spending visibility.", "Example: checks cash runway.") },
  { id: "medical", name: "Medical", help: help("Supports healthcare operations.", "Clearer patient and clinic workflows.", "Example: prepares visit summaries.") },
  { id: "construction", name: "Construction", help: help("Supports building projects and sites.", "Fewer missed site details.", "Example: tracks permit checklists.") },
  { id: "beauty", name: "Beauty", help: help("Supports salons and beauty studios.", "Smoother bookings and client care.", "Example: suggests rebooking times.") },
  { id: "manufacturing", name: "Manufacturing", help: help("Supports production floors.", "Faster operational answers.", "Example: explains a production delay.") },
  { id: "education", name: "Education", help: help("Supports learning and training.", "Clearer lessons and onboarding.", "Example: builds a short study plan.") },
  { id: "retail", name: "Retail", help: help("Supports stores and product sales.", "Better product answers for shoppers.", "Example: recommends matching items.") },
  { id: "hospitality", name: "Hospitality", help: help("Supports hotels and guest services.", "Warmer guest experiences.", "Example: prepares welcome notes.") },
  { id: "real_estate", name: "Real Estate", help: help("Supports property sales and rentals.", "Faster listing and viewing help.", "Example: summarizes a property brief.") },
  { id: "crypto", name: "Crypto", help: help("Supports digital asset operations.", "Clearer market and treasury answers.", "Example: explains a wallet activity summary.") },
  { id: "agriculture", name: "Agriculture", help: help("Supports farms and field operations.", "Better seasonal planning help.", "Example: reviews crop checklist notes.") },
  { id: "custom", name: "Custom", help: help("Define any profession you need.", "Fits unique businesses.", "Example: Fleet Operations Specialist.") },
];

export type SpecNode = { id: string; name: string; children?: SpecNode[] };

export const SPECIALIZATION_TREE: Record<string, SpecNode[]> = {
  medical: [
    {
      id: "dentistry",
      name: "Dentistry",
      children: [
        { id: "implantology", name: "Implantology" },
        { id: "orthodontics", name: "Orthodontics" },
        { id: "therapy", name: "Therapy" },
        { id: "surgery", name: "Surgery" },
      ],
    },
    {
      id: "general_practice",
      name: "General Practice",
      children: [
        { id: "family_medicine", name: "Family Medicine" },
        { id: "preventive_care", name: "Preventive Care" },
      ],
    },
  ],
  law: [
    {
      id: "corporate",
      name: "Corporate",
      children: [
        { id: "contracts", name: "Contracts" },
        { id: "compliance", name: "Compliance" },
      ],
    },
  ],
  sales: [
    {
      id: "outbound",
      name: "Outbound",
      children: [
        { id: "lead_qualification", name: "Lead Qualification" },
        { id: "demo_follow_up", name: "Demo Follow-up" },
      ],
    },
  ],
  finance: [
    {
      id: "treasury",
      name: "Treasury",
      children: [
        { id: "cash_flow", name: "Cash Flow" },
        { id: "forecasting", name: "Forecasting" },
      ],
    },
  ],
  beauty: [
    {
      id: "salon",
      name: "Salon Operations",
      children: [
        { id: "booking", name: "Booking" },
        { id: "client_care", name: "Client Care" },
      ],
    },
  ],
  construction: [
    {
      id: "site",
      name: "Site Operations",
      children: [
        { id: "permits", name: "Permits" },
        { id: "safety", name: "Safety" },
      ],
    },
  ],
  default: [
    {
      id: "general",
      name: "General",
      children: [
        { id: "operations", name: "Operations" },
        { id: "advisory", name: "Advisory" },
      ],
    },
  ],
};

export const KNOWLEDGE_SOURCES = [
  { id: "crm", name: "CRM", help: help("Customer records and conversations.", "AI answers with real client context.", "Example: recalls the latest deal stage.", "What it is: your customer database.") },
  { id: "erp", name: "ERP", help: help("Company operations and inventory systems.", "Answers reflect how the business runs day to day.", "Example: checks stock availability.", "What it is: core business systems.") },
  { id: "documents", name: "Documents", help: help("Shared files and folders.", "Finds answers inside company files.", "Example: opens the onboarding pack.", "What it is: your document library.") },
  { id: "pdf", name: "PDF", help: help("PDF files such as manuals and contracts.", "Reads locked-in documents safely.", "Example: summarizes a policy PDF.", "What it is: portable document files.") },
  { id: "word", name: "Word", help: help("Word documents and drafts.", "Helps with written procedures and letters.", "Example: rewrites a client letter.", "What it is: editable text documents.") },
  { id: "excel", name: "Excel", help: help("Spreadsheets and tables.", "Works with numbers and lists.", "Example: explains a pricing sheet.", "What it is: spreadsheet data.") },
  { id: "knowledge_base", name: "Knowledge Base", help: help("Approved company answers and playbooks.", "Keeps replies consistent.", "Example: uses the refund policy article.", "What it is: curated Q&A knowledge.") },
  { id: "email", name: "Email", help: help("Business email threads.", "Understands recent conversations.", "Example: drafts a reply to a supplier.", "What it is: your mailbox context.") },
  { id: "calendar", name: "Calendar", help: help("Meetings and schedules.", "Plans around real availability.", "Example: finds an open slot tomorrow.", "What it is: your schedule.") },
  { id: "telegram", name: "Telegram", help: help("Telegram chats and bots.", "Helps where your team already talks.", "Example: answers a channel question.", "What it is: Telegram messaging.") },
  { id: "marketplace", name: "Marketplace", help: help("Listings, offers, and marketplace activity.", "Supports selling and buying flows.", "Example: reviews a new listing draft.", "What it is: marketplace data.") },
  { id: "custom", name: "Custom Sources", help: help("Any other source you connect later.", "Fits unique tools.", "Example: a proprietary catalog API.", "What it is: your custom data source.") },
];

export const SKILLS = [
  { id: "answer_questions", name: "Answer Questions", help: help("Replies to people in clear language.", "Faster everyday support.", "Example: answers «What is our refund window?»") },
  { id: "analyze_documents", name: "Analyze Documents", help: help("Reads and explains files.", "Saves hours of manual reading.", "Example: highlights key clauses in a contract.") },
  { id: "create_reports", name: "Create Reports", help: help("Builds summaries and reports.", "Ready-to-share updates.", "Example: weekly sales snapshot.") },
  { id: "create_contracts", name: "Create Contracts", help: help("Prepares contract drafts.", "Speeds legal paperwork starts.", "Example: service agreement template fill.") },
  { id: "calendar", name: "Calendar", help: help("Works with meetings and reminders.", "Fewer scheduling mistakes.", "Example: books a follow-up call.") },
  { id: "crm_operations", name: "CRM Operations", help: help("Updates and uses CRM records.", "Keeps customer data fresh.", "Example: logs a call outcome.") },
  { id: "workflow", name: "Workflow", help: help("Starts and follows business workflows.", "Work moves without waiting.", "Example: launches onboarding flow.") },
  { id: "automation", name: "Automation", help: help("Triggers repeatable actions.", "Less repetitive clicking.", "Example: auto-sends a welcome pack.") },
  { id: "analytics", name: "Analytics", help: help("Finds patterns in numbers and activity.", "Clearer decisions.", "Example: spots a drop in conversions.") },
  { id: "recommendations", name: "Recommendations", help: help("Suggests next best actions.", "Guidance without guesswork.", "Example: recommends which lead to call first.") },
  { id: "learning", name: "Learning", help: help("Improves from feedback over time.", "Gets more useful with use.", "Example: remembers preferred report format.") },
  { id: "custom", name: "Custom", help: help("Add a unique ability.", "Fits special processes.", "Example: «Generate packing slips».") },
];

export const PERMISSIONS = [
  { id: "read_crm", name: "Read CRM", help: help("Look at customer records.", "Informed answers.", "Example: view a contact card.") },
  { id: "create_records", name: "Create Records", help: help("Add new records.", "Captures new information quickly.", "Example: create a lead.") },
  { id: "update_records", name: "Update Records", help: help("Change existing records.", "Keeps data accurate.", "Example: update deal stage.") },
  { id: "delete_records", name: "Delete Records", help: help("Remove records when allowed.", "Cleans outdated entries.", "Example: archive a duplicate contact.") },
  { id: "read_knowledge", name: "Read Knowledge", help: help("Use the knowledge base.", "Consistent answers.", "Example: open a policy article.") },
  { id: "launch_workflow", name: "Launch Workflow", help: help("Start approved workflows.", "Moves work forward.", "Example: start invoice approval.") },
  { id: "send_notifications", name: "Send Notifications", help: help("Notify people.", "Keeps teams informed.", "Example: ping sales about a hot lead.") },
  { id: "access_calendar", name: "Access Calendar", help: help("See and use calendar data.", "Reliable scheduling.", "Example: check free slots.") },
  { id: "access_documents", name: "Access Documents", help: help("Open document libraries.", "Answers from real files.", "Example: open a proposal draft.") },
  { id: "access_email", name: "Access Email", help: help("Use email context.", "Better conversation continuity.", "Example: draft a reply.") },
];

export const COMMUNICATION_STYLES = [
  { id: "business_professional", name: "Business Professional", sample: "Good day. I can prepare a clear summary for your team." },
  { id: "expert", name: "Expert", sample: "Based on the available records, here is the precise recommendation." },
  { id: "friendly", name: "Friendly", sample: "Happy to help! Here’s a simple way to look at it." },
  { id: "best_friend", name: "Best Friend", sample: "I’ve got you — let’s figure this out together." },
  { id: "best_girlfriend", name: "Best Girlfriend", sample: "I’m right here with you. Tell me what you need." },
  { id: "mentor", name: "Mentor", sample: "Let’s take this one step at a time so it stays clear." },
  { id: "energetic", name: "Energetic", sample: "Great timing! Let’s move this forward." },
  { id: "direct", name: "Direct", sample: "Next action: confirm the record, then send the update." },
  { id: "without_formalities", name: "Without Formalities", sample: "Sure — here’s the short version." },
  { id: "very_informal", name: "Very Informal", sample: "Yep, easy — try this." },
  { id: "technical", name: "Technical", sample: "Map the CRM field to workflow step 3, then relaunch." },
  { id: "short", name: "Short", sample: "Done. Next?" },
  { id: "detailed", name: "Detailed", sample: "Here’s a full walkthrough with each step explained." },
];

export type AgentDraft = {
  slot: number;
  name: string;
  nameGender: "male" | "female" | "neutral";
  profession: string | null;
  professionCustom: string;
  specialization: string[];
  knowledge: string[];
  skills: string[];
  permissions: string[];
  personality: {
    gender: "male" | "female" | "neutral";
    communicationStyle: string;
    professionalTone: string;
    conversationStyle: string;
  };
};

export function emptyAgent(slot: number): AgentDraft {
  return {
    slot,
    name: "",
    nameGender: "neutral",
    profession: null,
    professionCustom: "",
    specialization: [],
    knowledge: [],
    skills: [],
    permissions: [],
    personality: {
      gender: "neutral",
      communicationStyle: "business_professional",
      professionalTone: "balanced",
      conversationStyle: "ask_clarify",
    },
  };
}
