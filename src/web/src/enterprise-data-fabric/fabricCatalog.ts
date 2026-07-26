/**
 * Enterprise Data Fabric catalog — Sprint 33.3.
 * Entity graph over existing Knowledge / CRM / Twin / Workflow / Integrations.
 * No new Database Engine / Knowledge Engine / AI Core.
 */

export type FabricEntityKind =
  | "company"
  | "user"
  | "ai"
  | "client"
  | "deal"
  | "document"
  | "workflow"
  | "knowledge"
  | "integration";

export type FabricEntity = {
  id: string;
  kind: FabricEntityKind;
  label: string;
  detail: string;
  route?: string;
  missing?: boolean;
  problem?: boolean;
};

export type FabricEdge = {
  id: string;
  from: string;
  to: string;
  label: string;
};

/** Canonical entity nodes for the Enterprise Graph. */
export const FABRIC_ENTITIES: FabricEntity[] = [
  {
    id: "company",
    kind: "company",
    label: "Companies",
    detail: "Organization / tenant",
    route: "/identity/organizations",
  },
  {
    id: "users",
    kind: "user",
    label: "Users",
    detail: "Identity / roles",
    route: "/identity/users",
  },
  {
    id: "ai_team",
    kind: "ai",
    label: "AI Team",
    detail: "Specialists & Concierge",
    route: "/platform-builder/ai-team",
  },
  {
    id: "clients",
    kind: "client",
    label: "Clients",
    detail: "CRM accounts",
    route: "/workspace/crm",
  },
  {
    id: "deals",
    kind: "deal",
    label: "Deals",
    detail: "Pipeline opportunities",
    route: "/workspace/crm",
  },
  {
    id: "documents",
    kind: "document",
    label: "Documents",
    detail: "Docs workspace",
    route: "/workspace/docs",
  },
  {
    id: "workflows",
    kind: "workflow",
    label: "Workflows",
    detail: "Automation templates",
    route: "/platform-builder/workflow-center",
  },
  {
    id: "knowledge",
    kind: "knowledge",
    label: "Knowledge",
    detail: "Knowledge Base / EKG",
    route: "/platform-builder/knowledge",
  },
  {
    id: "integrations",
    kind: "integration",
    label: "Integrations",
    detail: "Integration Hub",
    route: "/platform-builder/integrations",
  },
];

/** Structural edges for the org data model. */
export const FABRIC_EDGES: FabricEdge[] = [
  { id: "e_co_users", from: "company", to: "users", label: "employs" },
  { id: "e_co_ai", from: "company", to: "ai_team", label: "operates" },
  { id: "e_co_clients", from: "company", to: "clients", label: "serves" },
  { id: "e_clients_deals", from: "clients", to: "deals", label: "owns" },
  { id: "e_deals_docs", from: "deals", to: "documents", label: "produces" },
  { id: "e_docs_kb", from: "documents", to: "knowledge", label: "indexes" },
  { id: "e_kb_wf", from: "knowledge", to: "workflows", label: "guides" },
  { id: "e_wf_ai", from: "workflows", to: "ai_team", label: "executes" },
  { id: "e_ai_int", from: "ai_team", to: "integrations", label: "calls" },
  { id: "e_users_ai", from: "users", to: "ai_team", label: "delegates" },
  { id: "e_int_clients", from: "integrations", to: "clients", label: "syncs" },
  { id: "e_deals_wf", from: "deals", to: "workflows", label: "triggers" },
];

/** Knowledge connection chain (Section 4). */
export const KNOWLEDGE_CHAIN: Array<{ id: string; label: string }> = [
  { id: "knowledge", label: "Knowledge" },
  { id: "documents", label: "Documents" },
  { id: "clients", label: "CRM" },
  { id: "workflows", label: "Workflow" },
  { id: "ai_team", label: "AI Team" },
  { id: "twin", label: "Digital Twin" },
];

export const KIND_LABEL: Record<FabricEntityKind, string> = {
  company: "Company",
  user: "User",
  ai: "AI Team",
  client: "Client",
  deal: "Deal",
  document: "Document",
  workflow: "Workflow",
  knowledge: "Knowledge",
  integration: "Integration",
};

export function getFabricEntity(id: string): FabricEntity | undefined {
  return FABRIC_ENTITIES.find((e) => e.id === id);
}
