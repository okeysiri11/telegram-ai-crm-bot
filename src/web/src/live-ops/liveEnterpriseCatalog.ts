/**
 * Live Enterprise catalog — Sprint 32.3.4.
 * Client-side labels / health targets only. No new engines.
 */

export type ActivityKind =
  | "ai"
  | "crm"
  | "client"
  | "deal"
  | "task"
  | "automation"
  | "notification"
  | "document"
  | "system";

export type LiveActivityItem = {
  id: string;
  kind: ActivityKind;
  title: string;
  detail: string;
  at: string;
  source: "mission_control" | "operations" | "notifications" | "recent" | "seed";
  moduleHint?: string;
};

export type HealthServiceId =
  | "ai_core"
  | "crm"
  | "analytics"
  | "documents"
  | "integrations"
  | "notifications"
  | "knowledge"
  | "mission_control";

export type HealthProbe = {
  id: HealthServiceId;
  label: string;
  healthUrl: string;
};

/** Enterprise health targets — existing hub / PB endpoints only. */
export const ENTERPRISE_HEALTH_PROBES: HealthProbe[] = [
  { id: "ai_core", label: "AI Core", healthUrl: "/api/platform-builder/v1/mission-control/status" },
  { id: "crm", label: "CRM", healthUrl: "/api/platform-builder/v1/mission-control/status" },
  { id: "analytics", label: "Analytics", healthUrl: "/api/platform-builder/v1/intelligence/health" },
  { id: "documents", label: "Documents", healthUrl: "/api/platform-builder/v1/digital-twin/knowledge" },
  { id: "integrations", label: "Integrations", healthUrl: "/api/enterprise-obs/v1/health" },
  { id: "notifications", label: "Notification Center", healthUrl: "/api/enterprise-obs/v1/health" },
  { id: "knowledge", label: "Knowledge Base", healthUrl: "/api/platform-builder/v1/digital-twin/knowledge" },
  { id: "mission_control", label: "Mission Control", healthUrl: "/api/platform-builder/v1/mission-control/status" },
];

/** Fallback feed when APIs are quiet — keeps the platform feeling alive. */
export const SEED_ACTIVITY: LiveActivityItem[] = [
  {
    id: "seed_ai_doc",
    kind: "ai",
    title: "AI создал документ",
    detail: "Brief по открытым сделкам",
    at: new Date(Date.now() - 4 * 60_000).toISOString(),
    source: "seed",
    moduleHint: "ai",
  },
  {
    id: "seed_crm",
    kind: "crm",
    title: "CRM обновлена",
    detail: "Pipeline sync",
    at: new Date(Date.now() - 9 * 60_000).toISOString(),
    source: "seed",
    moduleHint: "crm",
  },
  {
    id: "seed_client",
    kind: "client",
    title: "Новый клиент",
    detail: "Lead → Qualified",
    at: new Date(Date.now() - 18 * 60_000).toISOString(),
    source: "seed",
    moduleHint: "crm",
  },
  {
    id: "seed_deal",
    kind: "deal",
    title: "Новая сделка",
    detail: "Deal #1842",
    at: new Date(Date.now() - 26 * 60_000).toISOString(),
    source: "seed",
    moduleHint: "sales",
  },
  {
    id: "seed_task",
    kind: "task",
    title: "Новая задача",
    detail: "Подтвердить recommendation",
    at: new Date(Date.now() - 35 * 60_000).toISOString(),
    source: "seed",
    moduleHint: "hub",
  },
  {
    id: "seed_auto",
    kind: "automation",
    title: "Завершена автоматизация",
    detail: "Follow-up batch · 12",
    at: new Date(Date.now() - 48 * 60_000).toISOString(),
    source: "seed",
    moduleHint: "ai",
  },
];

export const LIVE_POLL_MS = 20_000;
