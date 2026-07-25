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

export const CONCIERGE_WIZARD_STEPS = [
  "Concierge Identity",
  "Concierge Role",
  "Organization Access",
  "AI Orchestration",
  "Proactive Assistance",
  "Owner Relationship",
  "Smart Recommendations",
  "Summary",
  "Create",
] as const;

export const AVATARS = [
  { id: "avatar_exec", name: "Executive", emoji: "🧑‍💼" },
  { id: "avatar_guide", name: "Guide", emoji: "🧭" },
  { id: "avatar_spark", name: "Spark", emoji: "✨" },
  { id: "avatar_shield", name: "Trusted", emoji: "🛡️" },
];

export const VOICE_PROFILES = [
  { id: "warm", name: "Warm" },
  { id: "clear", name: "Clear" },
  { id: "confident", name: "Confident" },
  { id: "soft", name: "Soft" },
];

export const COMMUNICATION_STYLES = [
  { id: "business_executive", name: "Business Executive", sample: "Good morning. Here is your priority brief for today." },
  { id: "professional", name: "Professional", sample: "I’ve prepared a clear update on today’s key items." },
  { id: "friendly", name: "Friendly", sample: "Happy to help — here’s a simple overview." },
  { id: "mentor", name: "Mentor", sample: "Let’s walk through this together, one step at a time." },
  { id: "best_friend", name: "Best Friend", sample: "I’ve got you — here’s what matters most right now." },
  { id: "best_girlfriend", name: "Best Girlfriend", sample: "I’m right here with you. Let’s make today feel lighter." },
  { id: "direct", name: "Direct", sample: "Three priorities: close the deal, review cash, confirm the meeting." },
  { id: "without_formalities", name: "Without Formalities", sample: "Quick take — here’s what needs attention." },
  { id: "very_informal", name: "Very Informal", sample: "Hey — easy wins for today are right here." },
  { id: "technical", name: "Technical", sample: "Route CRM lead scoring to the Sales specialist, then open analytics." },
  { id: "calm", name: "Calm", sample: "Take a breath. Here’s a steady plan for the morning." },
  { id: "energetic", name: "Energetic", sample: "Let’s go — your opportunities are lining up!" },
];

export const ROLES = [
  { id: "executive_assistant", name: "Executive Assistant", help: help("Supports leadership with schedules, briefs, and follow-ups.", "Keeps the owner focused on decisions, not busywork.", "Example: prepares a morning meeting pack.") },
  { id: "business_concierge", name: "Business Concierge", help: help("Guides people across the organization with helpful direction.", "Faster answers and smoother handoffs between teams.", "Example: routes a contract question to Legal AI.") },
  { id: "personal_concierge", name: "Personal Concierge", help: help("Stays close to the owner’s preferences and daily rhythm.", "Feels personal and attentive.", "Example: reminds about a preferred weekly review time.") },
  { id: "operations_manager", name: "Operations Manager", help: help("Watches workflows, tasks, and operational signals.", "Fewer missed follow-ups across departments.", "Example: flags overdue approvals.") },
  { id: "business_advisor", name: "Business Advisor", help: help("Offers thoughtful guidance from organization activity.", "Better strategic conversations with less preparation.", "Example: suggests focusing on high-margin opportunities.") },
  { id: "ceo_assistant", name: "CEO Assistant", help: help("Acts as a trusted partner for executive priorities.", "Clear leadership visibility across the company.", "Example: builds an executive report before the board call.") },
  { id: "custom", name: "Custom", help: help("Define a Concierge role unique to your organization.", "Fits any operating style.", "Example: Clinic Concierge for medical practices.") },
];

export const ORG_ACCESS = [
  { id: "crm", name: "CRM", help: help("Customer records and pipeline.", "Concierge understands clients and deals.", "Example: checks open opportunities.", "What it is: customer system.") },
  { id: "erp", name: "ERP", help: help("Core operations and resources.", "Answers reflect how the business runs.", "Example: reviews inventory signals.", "What it is: operations system.") },
  { id: "documents", name: "Documents", help: help("Company files and folders.", "Finds important papers quickly.", "Example: opens the latest proposal.", "What it is: document library.") },
  { id: "knowledge", name: "Knowledge", help: help("Approved company knowledge.", "Consistent guidance for everyone.", "Example: uses the refund policy.", "What it is: knowledge base.") },
  { id: "ai_registry", name: "AI Registry", help: help("Directory of AI Specialists.", "Concierge can find the right expert.", "Example: invites Sales AI to help.", "What it is: specialist registry.") },
  { id: "workflow_engine", name: "Workflow Engine", help: help("Business process engine.", "Starts and follows work flows.", "Example: launches onboarding.", "What it is: workflow system.") },
  { id: "analytics", name: "Analytics", help: help("Business metrics and trends.", "Clearer insights for decisions.", "Example: highlights conversion drop.", "What it is: analytics.") },
  { id: "calendar", name: "Calendar", help: help("Meetings and schedule.", "Reliable planning support.", "Example: prepares tomorrow’s agenda.", "What it is: calendar.") },
  { id: "tasks", name: "Tasks", help: help("To-dos and assignments.", "Keeps work moving.", "Example: suggests next owner action.", "What it is: task list.") },
  { id: "marketplace", name: "Marketplace", help: help("Listings and marketplace activity.", "Supports growth opportunities.", "Example: flags a hot listing.", "What it is: marketplace.") },
  { id: "notifications", name: "Notifications", help: help("Alerts and messages.", "Important news reaches people in time.", "Example: notifies about a deadline.", "What it is: notifications.") },
  { id: "automation", name: "Automation", help: help("Repeatable automated actions.", "Less manual busywork.", "Example: triggers a welcome sequence.", "What it is: automation.") },
  { id: "dashboards", name: "Dashboards", help: help("Visual business boards.", "Quick understanding of status.", "Example: opens executive dashboard.", "What it is: dashboards.") },
  { id: "departments", name: "Departments", help: help("Organization departments and teams.", "Coordinates across the company map.", "Example: routes a request to Finance.", "What it is: department map.") },
];

export const ORCHESTRATION = [
  { id: "delegate_tasks", name: "Delegate tasks", help: help("Hands work to the right specialist.", "Owner stays focused.", "Example: asks Legal AI to review a contract.") },
  { id: "call_specialists", name: "Call Specialists", help: help("Brings specialists into the conversation.", "Faster expert answers.", "Example: invites Finance AI for a cash question.") },
  { id: "monitor_specialists", name: "Monitor Specialists", help: help("Watches specialist progress.", "Fewer stalled tasks.", "Example: notices a report still pending.") },
  { id: "coordinate_team", name: "Coordinate Team", help: help("Aligns several specialists as a team.", "Smoother multi-expert work.", "Example: Sales + Marketing joint brief.") },
  { id: "summarize_discussions", name: "Summarize Discussions", help: help("Turns long chats into clear takeaways.", "Saves reading time.", "Example: summary of a specialist huddle.") },
  { id: "recommend_specialists", name: "Recommend Specialists", help: help("Suggests who should help next.", "Right expert, faster.", "Example: recommends Construction AI for permits.") },
  { id: "prepare_meetings", name: "Prepare Meetings", help: help("Builds agendas and prep packs.", "Meetings start ready.", "Example: CEO briefing before standup.") },
  { id: "create_executive_reports", name: "Create Executive Reports", help: help("Produces leadership-ready reports.", "Better visibility.", "Example: weekly organization digest.") },
];

export const PROACTIVE = [
  { id: "morning_briefing", name: "Morning Briefing" },
  { id: "evening_summary", name: "Evening Summary" },
  { id: "important_reminders", name: "Important Reminders" },
  { id: "upcoming_meetings", name: "Upcoming Meetings" },
  { id: "task_suggestions", name: "Task Suggestions" },
  { id: "business_opportunities", name: "Business Opportunities" },
  { id: "organization_insights", name: "Organization Insights" },
  { id: "performance_highlights", name: "Performance Highlights" },
  { id: "daily_digest", name: "Daily Digest" },
];

export const OWNER_RELATIONSHIPS = [
  { id: "only_when_requested", name: "Only when requested", help: help("Speaks when asked.", "Quiet and respectful.", "Example: waits for owner prompts.") },
  { id: "balanced", name: "Balanced", help: help("Helpful without overwhelming.", "Comfortable everyday support.", "Example: a few timely nudges.") },
  { id: "highly_proactive", name: "Highly Proactive", help: help("Actively brings useful updates.", "Owner stays ahead.", "Example: morning and evening outreach.") },
  { id: "executive_assistant", name: "Executive Assistant", help: help("Protects the owner’s time and priorities.", "Executive-grade support.", "Example: filters noise before it reaches the owner.") },
  { id: "business_partner", name: "Business Partner", help: help("Thinks with the owner about outcomes.", "Collaborative decisions.", "Example: discusses strategy options.") },
  { id: "daily_strategic_advisor", name: "Daily Strategic Advisor", help: help("Offers daily strategic perspective.", "Continuous leadership clarity.", "Example: daily focus recommendation.") },
];

export const RECOMMENDATIONS = [
  { id: "recommend_specialists", name: "Recommend Specialists" },
  { id: "recommend_workflows", name: "Recommend Workflows" },
  { id: "recommend_automations", name: "Recommend Automations" },
  { id: "recommend_dashboards", name: "Recommend Dashboards" },
  { id: "recommend_reports", name: "Recommend Reports" },
  { id: "recommend_knowledge", name: "Recommend Knowledge" },
  { id: "recommend_vertical_expansion", name: "Recommend Vertical Expansion" },
];

export type ConciergeDraft = {
  name: string;
  avatar: string;
  gender: "male" | "female" | "neutral";
  voiceProfile: string;
  communicationStyle: string;
  role: string | null;
  roleCustom: string;
  organizationAccess: string[];
  orchestration: string[];
  proactive: string[];
  ownerRelationship: string;
  recommendations: string[];
};

export function emptyDraft(): ConciergeDraft {
  return {
    name: "",
    avatar: "avatar_exec",
    gender: "neutral",
    voiceProfile: "clear",
    communicationStyle: "professional",
    role: null,
    roleCustom: "",
    organizationAccess: [],
    orchestration: [],
    proactive: [],
    ownerRelationship: "balanced",
    recommendations: [],
  };
}
