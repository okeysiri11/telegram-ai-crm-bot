import type { SearchDocument } from "../types";

let documents: SearchDocument[] = [
  { id: "idx_mod_ws", category: "modules", title: "Workspace", path: "/workspace", tokens: ["workspace", "home"], rankBoost: 10 },
  { id: "idx_user", category: "users", title: "Alex Owner", path: "/identity/users", tokens: ["alex", "owner", "user"], rankBoost: 5 },
  { id: "idx_org", category: "organizations", title: "Demo Corp", path: "/identity/organizations", tokens: ["demo", "corp", "org"], rankBoost: 5 },
  { id: "idx_proj", category: "projects", title: "Enterprise Web", path: "/workspace/list", tokens: ["project", "web"], rankBoost: 4 },
  { id: "idx_doc", category: "documents", title: "Security Policy", path: "/workspace/docs", tokens: ["security", "policy", "doc", "documents"], rankBoost: 3 },
  { id: "idx_crm", category: "crm", title: "CRM Pipeline", path: "/workspace/crm", tokens: ["crm", "pipeline", "leads"], rankBoost: 6 },
  { id: "idx_erp", category: "erp", title: "ERP Inventory", path: "/workspace/erp", tokens: ["erp", "inventory"], rankBoost: 6 },
  { id: "idx_fin", category: "finance", title: "Finance Summary", path: "/workspace/finance", tokens: ["finance", "billing"], rankBoost: 6 },
  { id: "idx_hr", category: "hr", title: "HR Directory", path: "/workspace/hr", tokens: ["hr", "people"], rankBoost: 4 },
  { id: "idx_ai", category: "ai_agents", title: "Ops Copilot", path: "/workspace/ai", tokens: ["ai", "copilot", "agent"], rankBoost: 8 },
  { id: "idx_wf", category: "workflows", title: "Invoice Approval", path: "/workspace/workflows/invoice", tokens: ["workflow", "invoice"], rankBoost: 7 },
  { id: "idx_rep", category: "reports", title: "Weekly KPI", path: "/workspace/reports/weekly", tokens: ["report", "kpi", "weekly"], rankBoost: 5 },
  { id: "idx_task", category: "tasks", title: "Review Migration", path: "/workspace?task=migration", tokens: ["task", "migration"], rankBoost: 4 },
  { id: "idx_dash_exec", category: "dashboards", title: "Executive Dashboard", path: "/dashboard?mode=executive", tokens: ["dashboard", "executive", "kpi"], rankBoost: 10 },
  { id: "idx_dash_main", category: "dashboards", title: "Dashboard", path: "/dashboard", tokens: ["dashboard", "home", "command"], rankBoost: 10 },
  { id: "idx_first_entry", category: "applications", title: "First Entry", path: "/onboarding/first-entry", tokens: ["first", "entry", "onboarding"], rankBoost: 8 },
  { id: "idx_mission_control", category: "dashboards", title: "Mission Control", path: "/platform-builder/mission-control", tokens: ["mission", "control", "mc", "ops"], rankBoost: 10 },
  { id: "idx_enterprise_city", category: "applications", title: "Enterprise City", path: "/enterprise-city", tokens: ["city", "enterprise", "map"], rankBoost: 9 },
  { id: "idx_builder_studio", category: "applications", title: "AI Builder Studio", path: "/platform-builder/builder-studio", tokens: ["builder", "studio", "ai"], rankBoost: 9 },
  { id: "idx_mkt", category: "marketplace", title: "Enterprise Marketplace", path: "/platform-builder/solution-hub", tokens: ["marketplace", "solutions", "hub", "packs"], rankBoost: 8 },
  { id: "idx_twin", category: "applications", title: "Enterprise Twin", path: "/enterprise-twin", tokens: ["twin", "digital", "organization", "mirror", "heatmap"], rankBoost: 9 },
  { id: "idx_integrations", category: "applications", title: "Integration Hub", path: "/platform-builder/integrations", tokens: ["integrations", "telegram", "webhook", "oauth", "api"], rankBoost: 8 },
  { id: "idx_runtime", category: "ai_agents", title: "AI Runtime Center", path: "/platform-builder/runtime", tokens: ["runtime", "queue", "orchestration", "jobs"], rankBoost: 9 },
  { id: "idx_data_fabric", category: "knowledge", title: "Enterprise Data Fabric", path: "/platform-builder/data-fabric", tokens: ["data", "fabric", "graph", "lineage", "knowledge"], rankBoost: 9 },
  { id: "idx_predictive", category: "dashboards", title: "Predictive Intelligence", path: "/platform-builder/predictive", tokens: ["predictive", "forecast", "scenario", "what-if"], rankBoost: 9 },
  { id: "idx_autonomy", category: "ai_agents", title: "Autonomy Center", path: "/platform-builder/autonomy", tokens: ["autonomy", "approval", "hitl", "governance"], rankBoost: 9 },
  { id: "idx_control_tower", category: "dashboards", title: "Enterprise Control Tower", path: "/platform-builder/control-tower", tokens: ["control", "tower", "executive", "overview", "ops"], rankBoost: 10 },
  { id: "idx_learning", category: "dashboards", title: "Self-Learning Enterprise", path: "/platform-builder/learning", tokens: ["learning", "optimize", "recommendations", "self-learning", "continuous"], rankBoost: 10 },
  { id: "idx_okr", category: "dashboards", title: "OKR Intelligence", path: "/platform-builder/okr", tokens: ["okr", "goals", "strategy", "kpi", "objectives"], rankBoost: 10 },
  { id: "idx_governance", category: "dashboards", title: "Enterprise Governance", path: "/platform-builder/governance", tokens: ["governance", "compliance", "policy", "audit", "security"], rankBoost: 10 },
  { id: "idx_user_ops", category: "users", title: "Ops Manager", path: "/identity/users", tokens: ["ops", "manager", "user", "people"], rankBoost: 4 },
  { id: "idx_ai_concierge", category: "ai_agents", title: "AI Concierge", path: "/platform-builder/concierge", tokens: ["concierge", "ai", "assistant"], rankBoost: 7 },
  { id: "idx_ai_team", category: "ai_agents", title: "AI Team Center", path: "/platform-builder/ai-team", tokens: ["ai", "team", "specialists"], rankBoost: 8 },
  { id: "idx_wf_center", category: "workflows", title: "Workflow Center", path: "/platform-builder/workflow-center", tokens: ["workflow", "automation", "center"], rankBoost: 8 },
  { id: "idx_doc_kb", category: "documents", title: "Knowledge Documents", path: "/workspace/docs", tokens: ["documents", "docs", "knowledge", "files"], rankBoost: 5 },
  { id: "idx_crm_clients", category: "crm", title: "CRM Clients", path: "/workspace/crm", tokens: ["clients", "crm", "deals", "pipeline"], rankBoost: 7 },
  { id: "idx_int_hub", category: "applications", title: "Integrations Control", path: "/platform-builder/integrations", tokens: ["integrations", "telegram", "oauth", "webhooks", "api keys"], rankBoost: 7 },
  { id: "idx_org_demo", category: "organizations", title: "Organization Mirror", path: "/identity/organizations", tokens: ["organization", "tenant", "company", "org"], rankBoost: 6 },
  { id: "idx_app", category: "applications", title: "Enterprise Hub", path: "/workspace", tokens: ["hub", "application"], rankBoost: 9 },
  { id: "idx_dash", category: "dashboards", title: "Personal Dashboard", path: "/workspace/dashboards", tokens: ["dashboard"], rankBoost: 7 },
  { id: "idx_wdg", category: "widgets", title: "Recent Activity Widget", path: "/command-center#recent_activity", tokens: ["widget", "activity"], rankBoost: 4 },
  { id: "idx_kb", category: "knowledge", title: "Knowledge Base", path: "/platform-builder/knowledge", tokens: ["knowledge", "base"], rankBoost: 6 },
];

export const searchIndex = {
  list(): SearchDocument[] {
    return [...documents];
  },
  upsert(doc: SearchDocument) {
    documents = [doc, ...documents.filter((d) => d.id !== doc.id)];
    return documents.length;
  },
  refresh() {
    // simulate background index update
    documents = documents.map((d) => ({ ...d, rankBoost: d.rankBoost }));
    return { updatedAt: new Date().toISOString(), count: documents.length };
  },
  categories() {
    return [...new Set(documents.map((d) => d.category))];
  },
};
