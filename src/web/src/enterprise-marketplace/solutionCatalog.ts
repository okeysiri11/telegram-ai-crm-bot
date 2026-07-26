/**
 * Enterprise Marketplace solution catalog — Sprint 32.9.
 * Composes Builder Studio / Workflow / Ecosystem IDs (no circular imports).
 * No new Marketplace Engine.
 */

import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";

export type MarketplaceCategory =
  | "ai_teams"
  | "workflows"
  | "skills"
  | "prompt_packs"
  | "ecosystem_templates"
  | "integrations"
  | "enterprise_hub";

export type SolutionInstallStatus = "available" | "installed" | "update" | "disabled" | "draft";

export type MarketplaceSolution = {
  id: string;
  title: string;
  description: string;
  category: MarketplaceCategory;
  ecosystems: string[];
  roles: string[];
  aiTeam: string[];
  workflows: string[];
  skills: string[];
  prompts: string[];
  templates: string[];
  rating: number;
  version: string;
  statusDefault?: SolutionInstallStatus;
  enterprisePack?: boolean;
};

export const MARKETPLACE_CATEGORIES: Array<{ id: MarketplaceCategory; label: string }> = [
  { id: "ai_teams", label: "AI Teams" },
  { id: "workflows", label: "Workflows" },
  { id: "skills", label: "Skills" },
  { id: "prompt_packs", label: "Prompt Packs" },
  { id: "ecosystem_templates", label: "Ecosystem Templates" },
  { id: "integrations", label: "Integrations" },
  { id: "enterprise_hub", label: "Enterprise Hub" },
];

const WF_IDS = BUSINESS_WORKFLOW_TEMPLATES.map((t) => t.id);
const SKILL_IDS = ["crm", "marketing", "sales", "legal", "analytics", "finance", "knowledge", "automation"];
const PROMPT_IDS = ["corp_brand", "corp_compliance", "user_brief", "user_crm", "fav_exec", "fav_handoff"];
const ECO_IDS = ["beauty", "legal", "cafe", "auto", "agro", "drone", "crypto"];

/** Enterprise packs for seven ecosystems (SECTION 7). */
const ENTERPRISE_PACKS: MarketplaceSolution[] = [
  {
    id: "pack_beauty",
    title: "Beauty Enterprise Pack",
    description: "AI Team + booking workflows + client-care prompts for salons.",
    category: "enterprise_hub",
    ecosystems: ["beauty"],
    roles: ["owner", "manager", "staff"],
    aiTeam: ["Concierge", "Marketing AI", "Sales AI"],
    workflows: ["new_client", "request"],
    skills: ["crm", "marketing", "sales"],
    prompts: PROMPT_IDS.slice(0, 3),
    templates: ["beauty"],
    rating: 4.8,
    version: "1.2.0",
    enterprisePack: true,
  },
  {
    id: "pack_legal",
    title: "Legal Enterprise Pack",
    description: "Contract review team, compliance prompts, legal workflows.",
    category: "enterprise_hub",
    ecosystems: ["legal"],
    roles: ["owner", "counsel", "paralegal"],
    aiTeam: ["Concierge", "Legal AI", "Analytics AI"],
    workflows: ["contract", "invoice"],
    skills: ["legal", "knowledge", "analytics"],
    prompts: ["corp_compliance", "fav_exec"],
    templates: ["legal"],
    rating: 4.7,
    version: "1.1.0",
    enterprisePack: true,
  },
  {
    id: "pack_cafe",
    title: "Cafe Enterprise Pack",
    description: "Ops + sales specialists for cafe / hospitality floors.",
    category: "enterprise_hub",
    ecosystems: ["cafe"],
    roles: ["owner", "manager"],
    aiTeam: ["Concierge", "Operations AI", "Sales AI"],
    workflows: ["request", "sale"],
    skills: ["crm", "automation", "sales"],
    prompts: ["corp_brand", "user_brief"],
    templates: ["cafe"],
    rating: 4.6,
    version: "1.0.0",
    enterprisePack: true,
  },
  {
    id: "pack_agro",
    title: "Agriculture Enterprise Pack",
    description: "Field ops, harvest workflows, agronomy knowledge pack.",
    category: "enterprise_hub",
    ecosystems: ["agro"],
    roles: ["owner", "agronomist", "manager"],
    aiTeam: ["Concierge", "Operations AI", "Analytics AI"],
    workflows: ["project", "maintenance"],
    skills: ["analytics", "automation", "knowledge"],
    prompts: ["user_brief", "fav_exec"],
    templates: ["agro"],
    rating: 4.5,
    version: "1.0.0",
    enterprisePack: true,
  },
  {
    id: "pack_auto",
    title: "Automotive Enterprise Pack",
    description: "Service CRM, dealership sales AI, maintenance workflows.",
    category: "enterprise_hub",
    ecosystems: ["auto"],
    roles: ["owner", "service_advisor", "sales"],
    aiTeam: ["Concierge", "Sales AI", "Operations AI"],
    workflows: ["new_client", "sale", "maintenance"],
    skills: ["crm", "sales", "automation"],
    prompts: ["user_crm", "corp_brand"],
    templates: ["auto"],
    rating: 4.7,
    version: "1.3.0",
    enterprisePack: true,
  },
  {
    id: "pack_drone",
    title: "Drone Enterprise Pack",
    description: "Fleet production AI, mission workflows, ops prompts.",
    category: "enterprise_hub",
    ecosystems: ["drone"],
    roles: ["owner", "fleet_ops"],
    aiTeam: ["Concierge", "Operations AI", "Analytics AI"],
    workflows: ["project", "maintenance"],
    skills: ["automation", "analytics", "knowledge"],
    prompts: ["fav_handoff", "fav_exec"],
    templates: ["drone"],
    rating: 4.4,
    version: "1.0.0",
    enterprisePack: true,
  },
  {
    id: "pack_bidex",
    title: "Bidex Enterprise Pack",
    description: "Crypto/treasury AI team, risk workflows, finance skills.",
    category: "enterprise_hub",
    ecosystems: ["crypto"],
    roles: ["owner", "cfo", "trader"],
    aiTeam: ["Concierge", "Finance AI", "Analytics AI", "Legal AI"],
    workflows: ["invoice", "contract"],
    skills: ["finance", "analytics", "legal"],
    prompts: ["corp_compliance", "fav_exec"],
    templates: ["crypto"],
    rating: 4.6,
    version: "1.1.0",
    enterprisePack: true,
  },
];

export const MARKETPLACE_SOLUTIONS: MarketplaceSolution[] = [
  {
    id: "team_sales_ops",
    title: "Sales + Ops AI Team",
    description: "Готовая команда Concierge · Sales · Ops для CRM follow-up.",
    category: "ai_teams",
    ecosystems: ["auto", "beauty", "cafe", "platform"],
    roles: ["owner", "sales", "manager"],
    aiTeam: ["Concierge", "Sales AI", "Operations AI"],
    workflows: ["new_client", "sale"],
    skills: ["crm", "sales", "automation"],
    prompts: ["user_crm", "fav_handoff"],
    templates: [],
    rating: 4.9,
    version: "2.0.0",
  },
  {
    id: "team_legal_finance",
    title: "Legal + Finance AI Team",
    description: "Договоры и счета под контролем Legal и Finance AI.",
    category: "ai_teams",
    ecosystems: ["legal", "crypto", "platform"],
    roles: ["owner", "counsel", "cfo"],
    aiTeam: ["Concierge", "Legal AI", "Finance AI"],
    workflows: ["contract", "invoice"],
    skills: ["legal", "finance", "knowledge"],
    prompts: ["corp_compliance"],
    templates: [],
    rating: 4.8,
    version: "1.4.0",
  },
  {
    id: "wf_new_client_pack",
    title: "New Client Workflow Pack",
    description: "Импорт workflow «Новый клиент» + связанные prompt packs.",
    category: "workflows",
    ecosystems: ["platform", "auto", "beauty", "cafe"],
    roles: ["owner", "manager"],
    aiTeam: ["Marketing AI", "Sales AI", "Analytics AI"],
    workflows: ["new_client"],
    skills: ["crm", "marketing", "sales"],
    prompts: ["user_crm", "corp_brand"],
    templates: [],
    rating: 4.7,
    version: "1.0.0",
  },
  {
    id: "wf_contract_pack",
    title: "Contract Approval Workflow",
    description: "Визуальный contract workflow из Enterprise Workflow Automation.",
    category: "workflows",
    ecosystems: ["legal", "platform"],
    roles: ["owner", "counsel"],
    aiTeam: ["Legal AI", "Finance AI"],
    workflows: ["contract"],
    skills: ["legal", "knowledge"],
    prompts: ["corp_compliance"],
    templates: [],
    rating: 4.6,
    version: "1.0.0",
  },
  {
    id: "skills_growth",
    title: "Growth Skill Pack",
    description: "CRM · Marketing · Sales domain skills из Builder Studio.",
    category: "skills",
    ecosystems: ["platform", "beauty", "cafe", "auto"],
    roles: ["owner", "marketing", "sales"],
    aiTeam: ["Marketing AI", "Sales AI"],
    workflows: ["sale"],
    skills: ["crm", "marketing", "sales"],
    prompts: ["corp_brand"],
    templates: [],
    rating: 4.5,
    version: "1.0.0",
  },
  {
    id: "skills_ops",
    title: "Ops Skill Pack",
    description: "Analytics · Automation · Knowledge packs.",
    category: "skills",
    ecosystems: ["platform", "agro", "drone"],
    roles: ["owner", "ops"],
    aiTeam: ["Operations AI", "Analytics AI"],
    workflows: ["project"],
    skills: ["analytics", "automation", "knowledge"],
    prompts: ["user_brief"],
    templates: [],
    rating: 4.4,
    version: "1.0.0",
  },
  {
    id: "prompts_exec",
    title: "Executive Prompt Pack",
    description: "Corporate + favorite prompts for leadership briefs.",
    category: "prompt_packs",
    ecosystems: ["platform"],
    roles: ["owner", "executive"],
    aiTeam: ["Concierge"],
    workflows: [],
    skills: ["analytics"],
    prompts: PROMPT_IDS,
    templates: [],
    rating: 4.8,
    version: "1.0.0",
  },
  {
    id: "tpl_all_ecosystems",
    title: "All Ecosystem Starters",
    description: "Быстрый доступ к семи ecosystem templates.",
    category: "ecosystem_templates",
    ecosystems: ECO_IDS,
    roles: ["owner"],
    aiTeam: ["Concierge"],
    workflows: WF_IDS.slice(0, 3),
    skills: SKILL_IDS.slice(0, 4),
    prompts: ["corp_brand"],
    templates: ECO_IDS,
    rating: 4.3,
    version: "1.0.0",
    statusDefault: "draft",
  },
  {
    id: "int_crm_mc",
    title: "CRM + Mission Control Bundle",
    description: "Интеграционный пакет: CRM workspace + Mission Control + notifications.",
    category: "integrations",
    ecosystems: ["platform"],
    roles: ["owner", "manager"],
    aiTeam: ["Concierge", "Sales AI"],
    workflows: ["new_client"],
    skills: ["crm", "automation"],
    prompts: ["user_crm"],
    templates: [],
    rating: 4.5,
    version: "1.0.0",
  },
  {
    id: "int_knowledge",
    title: "Knowledge + Prompt Bridge",
    description: "Связка Knowledge Base с corporate prompt packs.",
    category: "integrations",
    ecosystems: ["platform", "legal"],
    roles: ["owner", "knowledge_manager"],
    aiTeam: ["Concierge", "Legal AI"],
    workflows: ["contract"],
    skills: ["knowledge", "legal"],
    prompts: ["corp_compliance", "corp_brand"],
    templates: [],
    rating: 4.4,
    version: "1.0.0",
  },
  ...ENTERPRISE_PACKS,
];

export function getMarketplaceSolution(id: string): MarketplaceSolution | undefined {
  return MARKETPLACE_SOLUTIONS.find((s) => s.id === id);
}

export function solutionsByCategory(category: MarketplaceCategory | "all"): MarketplaceSolution[] {
  if (category === "all") return MARKETPLACE_SOLUTIONS;
  return MARKETPLACE_SOLUTIONS.filter((s) => s.category === category);
}
