/**
 * Sprint 32.1 — Built-in AI Agent catalog (AgentOS registry seed).
 * Projected into aiAgentRuntime + Agent Center. No parallel registry.
 */

export type DefaultAgentRole =
  | "owner"
  | "ceo"
  | "project_manager"
  | "developer"
  | "architect"
  | "lawyer"
  | "marketing"
  | "sales"
  | "support"
  | "accountant"
  | "production"
  | "construction"
  | "crypto"
  | "medical"
  | "research"
  | "designer"
  | "copywriter"
  | "business_analyst"
  | "image"
  | "video"
  | "audio"
  | "prompt"
  | "brand"
  | "workflow"
  | "publishing";

export type DefaultAgentDef = {
  id: string;
  role: DefaultAgentRole;
  name: string;
  nameRu: string;
  profession: string;
  specialization: string;
  capabilities: string[];
  studioHints: string[];
  /** Sprint 32.1 registry metadata */
  version: string;
  permissions: string[];
  marketplaceTag?: string;
};

export const DEFAULT_AGENTS: DefaultAgentDef[] = [
  {
    id: "agent_owner",
    role: "owner",
    name: "Owner AI",
    nameRu: "Владелец AI",
    profession: "Governance",
    specialization: "God Mode · fleet policy · kill-switch",
    capabilities: ["govern", "audit", "escalate"],
    studioHints: ["analytics"],
    version: "1.0.0",
    permissions: ["*", "ai_agents", "owner"],
    marketplaceTag: "executive",
  },
  {
    id: "agent_ceo",
    role: "ceo",
    name: "CEO AI",
    nameRu: "CEO AI",
    profession: "Executive",
    specialization: "Strategy · priorities · briefs",
    capabilities: ["strategy", "brief", "decide"],
    studioHints: ["analytics", "prompt"],
    version: "1.0.0",
    permissions: ["ai_agents", "strategy"],
    marketplaceTag: "executive",
  },
  {
    id: "agent_project_manager",
    role: "project_manager",
    name: "Project Manager AI",
    nameRu: "Менеджер проектов",
    profession: "Delivery",
    specialization: "Plans · milestones · handoffs",
    capabilities: ["plan", "assign", "track"],
    studioHints: ["creative", "publishing"],
    version: "1.0.0",
    permissions: ["ai_agents", "projects"],
  },
  {
    id: "agent_developer",
    role: "developer",
    name: "Developer AI",
    nameRu: "Разработчик",
    profession: "Engineering",
    specialization: "Code · APIs · platform tools",
    capabilities: ["code_assist", "debug", "docs"],
    studioHints: ["prompt", "assets"],
    version: "1.0.0",
    permissions: ["ai_agents", "code"],
  },
  {
    id: "agent_architect",
    role: "architect",
    name: "Architect AI",
    nameRu: "Архитектор",
    profession: "Architecture",
    specialization: "Systems · boundaries · ADRs",
    capabilities: ["design", "review", "adr"],
    studioHints: ["prompt", "analytics"],
    version: "1.0.0",
    permissions: ["ai_agents", "architecture"],
  },
  {
    id: "agent_lawyer",
    role: "lawyer",
    name: "Legal AI",
    nameRu: "Юрист",
    profession: "Legal",
    specialization: "Contracts · compliance · risk",
    capabilities: ["contract_review", "policy", "risk"],
    studioHints: ["prompt", "brand"],
    version: "1.0.0",
    permissions: ["ai_agents", "legal"],
  },
  {
    id: "agent_marketing",
    role: "marketing",
    name: "Marketing AI",
    nameRu: "Маркетолог",
    profession: "Growth",
    specialization: "Campaigns · funnels · brand",
    capabilities: ["campaign", "audience", "copy"],
    studioHints: ["ads", "reels", "brand"],
    version: "1.0.0",
    permissions: ["ai_agents", "marketing"],
  },
  {
    id: "agent_sales",
    role: "sales",
    name: "Sales AI",
    nameRu: "Продажи",
    profession: "Revenue",
    specialization: "Pipeline · outreach · CRM",
    capabilities: ["crm", "outreach", "deal"],
    studioHints: ["ads", "creative"],
    version: "1.0.0",
    permissions: ["ai_agents", "sales"],
  },
  {
    id: "agent_support",
    role: "support",
    name: "Support AI",
    nameRu: "Поддержка",
    profession: "Support",
    specialization: "Tickets · triage · replies",
    capabilities: ["triage", "reply", "escalate"],
    studioHints: ["prompt"],
    version: "1.0.0",
    permissions: ["ai_agents", "support"],
  },
  {
    id: "agent_accountant",
    role: "accountant",
    name: "Finance AI",
    nameRu: "Финансы",
    profession: "Finance",
    specialization: "Ledgers · reports · tax hints",
    capabilities: ["finance", "report", "reconcile"],
    studioHints: ["prompt"],
    version: "1.0.0",
    permissions: ["ai_agents", "finance"],
  },
  {
    id: "agent_production",
    role: "production",
    name: "Production AI",
    nameRu: "Продакшн",
    profession: "Creative Ops",
    specialization: "Image · video · publish queues",
    capabilities: ["generate", "render", "publish"],
    studioHints: ["image", "video", "reels", "voice"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
  {
    id: "agent_construction",
    role: "construction",
    name: "Construction AI",
    nameRu: "Строительство",
    profession: "Construction",
    specialization: "Plans · estimates · compliance",
    capabilities: ["estimate", "schedule", "safety"],
    studioHints: ["prompt", "presentation"],
    version: "1.0.0",
    permissions: ["ai_agents", "construction"],
  },
  {
    id: "agent_crypto",
    role: "crypto",
    name: "Crypto AI",
    nameRu: "Крипто",
    profession: "Digital Assets",
    specialization: "Wallets · risk · treasury hints",
    capabilities: ["risk", "treasury", "monitor"],
    studioHints: ["analytics", "prompt"],
    version: "1.0.0",
    permissions: ["ai_agents", "crypto"],
  },
  {
    id: "agent_medical",
    role: "medical",
    name: "Medical AI",
    nameRu: "Медицина",
    profession: "Healthcare",
    specialization: "Research assist · protocol hints (non-diagnostic)",
    capabilities: ["research", "summarize", "protocol"],
    studioHints: ["prompt"],
    version: "1.0.0",
    permissions: ["ai_agents", "medical"],
  },
  {
    id: "agent_research",
    role: "research",
    name: "Research AI",
    nameRu: "Исследования",
    profession: "R&D",
    specialization: "Sources · synthesis · briefs",
    capabilities: ["research", "synthesize", "cite"],
    studioHints: ["prompt", "analytics"],
    version: "1.0.0",
    permissions: ["ai_agents", "research"],
  },
  {
    id: "agent_designer",
    role: "designer",
    name: "Designer",
    nameRu: "Дизайнер",
    profession: "Design",
    specialization: "Visual systems · layouts · brand",
    capabilities: ["layout", "brand", "assets"],
    studioHints: ["image", "brand", "assets", "presentation"],
    version: "1.0.0",
    permissions: ["ai_agents", "design"],
  },
  {
    id: "agent_copywriter",
    role: "copywriter",
    name: "Copywriter",
    nameRu: "Копирайтер",
    profession: "Content",
    specialization: "Scripts · ads · social copy",
    capabilities: ["copy", "script", "localize"],
    studioHints: ["prompt", "ads", "reels", "voice"],
    version: "1.0.0",
    permissions: ["ai_agents", "content"],
  },
  {
    id: "agent_business_analyst",
    role: "business_analyst",
    name: "Business Analyst",
    nameRu: "Бизнес-аналитик",
    profession: "Analytics",
    specialization: "Requirements · KPIs · insights",
    capabilities: ["analyze", "kpi", "brief"],
    studioHints: ["analytics", "prompt"],
    version: "1.0.0",
    permissions: ["ai_agents", "analytics"],
  },
  // Production Studio specialists
  {
    id: "agent_image",
    role: "image",
    name: "Image Agent",
    nameRu: "Image Agent",
    profession: "Production",
    specialization: "Stills · variants · brand crops",
    capabilities: ["generate", "image"],
    studioHints: ["image"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
  {
    id: "agent_video",
    role: "video",
    name: "Video Agent",
    nameRu: "Video Agent",
    profession: "Production",
    specialization: "Clips · timelines · scenes",
    capabilities: ["generate", "video", "render"],
    studioHints: ["video", "reels"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
  {
    id: "agent_audio",
    role: "audio",
    name: "Audio Agent",
    nameRu: "Audio Agent",
    profession: "Production",
    specialization: "Voice · beds · mix",
    capabilities: ["generate", "audio", "voice"],
    studioHints: ["audio", "voice"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
  {
    id: "agent_prompt",
    role: "prompt",
    name: "Prompt Agent",
    nameRu: "Prompt Agent",
    profession: "Production",
    specialization: "Prompt craft · variables · versions",
    capabilities: ["prompt", "variables", "version"],
    studioHints: ["prompt"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
  {
    id: "agent_brand",
    role: "brand",
    name: "Brand Agent",
    nameRu: "Brand Agent",
    profession: "Production",
    specialization: "Brand kit · compliance · tone",
    capabilities: ["brand", "compliance", "tone"],
    studioHints: ["brand", "ads"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
  {
    id: "agent_workflow",
    role: "workflow",
    name: "Workflow Agent",
    nameRu: "Workflow Agent",
    profession: "Production",
    specialization: "Pipelines · approvals · handoffs",
    capabilities: ["pipeline", "approve", "delegate"],
    studioHints: ["creative", "publishing"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
  {
    id: "agent_publishing",
    role: "publishing",
    name: "Publishing Agent",
    nameRu: "Publishing Agent",
    profession: "Production",
    specialization: "Channels · schedule · publish",
    capabilities: ["publish", "schedule", "channel"],
    studioHints: ["publishing", "tiktok", "instagram", "youtube"],
    version: "1.0.0",
    permissions: ["ai_agents", "production"],
    marketplaceTag: "production",
  },
];

export function defaultAgentById(id: string): DefaultAgentDef | undefined {
  return DEFAULT_AGENTS.find((a) => a.id === id);
}

export function defaultAgentByRole(role: DefaultAgentRole): DefaultAgentDef | undefined {
  return DEFAULT_AGENTS.find((a) => a.role === role);
}

export function agentsByMarketplaceTag(tag: string): DefaultAgentDef[] {
  return DEFAULT_AGENTS.filter((a) => a.marketplaceTag === tag);
}
