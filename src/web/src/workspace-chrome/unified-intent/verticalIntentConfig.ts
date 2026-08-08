/**
 * Sprint 46.4 — vertical configs for UnifiedIntentBar (same UI, different scope).
 */

import type { VerticalIntentConfig } from "./unifiedIntentTypes";

const BASE: Omit<VerticalIntentConfig, "verticalId" | "contextLabel" | "searchScope"> = {
  availableActions: ["ask", "find", "create", "open", "run"],
};

export const VERTICAL_INTENT_CONFIGS: Record<string, VerticalIntentConfig> = {
  owner: {
    ...BASE,
    verticalId: "owner",
    contextLabel: "Вся платформа",
    searchScope: ["clients", "documents", "modules", "projects", "knowledge"],
    aiSpecialist: "concierge",
  },
  crm: {
    ...BASE,
    verticalId: "crm",
    contextLabel: "CRM",
    searchScope: ["clients", "leads", "deals"],
    aiSpecialist: "crm",
  },
  auto: {
    ...BASE,
    verticalId: "auto",
    contextLabel: "Авто",
    searchScope: ["vehicles", "clients", "leads", "deals"],
    aiSpecialist: "auto",
  },
  beauty: {
    ...BASE,
    verticalId: "beauty",
    contextLabel: "Beauty",
    searchScope: ["clients", "appointments", "content", "campaigns"],
    aiSpecialist: "beauty",
  },
  travel: {
    ...BASE,
    verticalId: "travel",
    contextLabel: "Travel",
    searchScope: ["clients", "tours", "bookings", "campaigns"],
    aiSpecialist: "travel",
  },
  crypto: {
    ...BASE,
    verticalId: "crypto",
    contextLabel: "Crypto",
    searchScope: ["clients", "deals", "otc"],
    aiSpecialist: "crypto",
  },
  agro: {
    ...BASE,
    verticalId: "agro",
    contextLabel: "Агро",
    searchScope: ["clients", "deals", "documents"],
    aiSpecialist: "agro",
  },
  drone: {
    ...BASE,
    verticalId: "drone",
    contextLabel: "Дроны",
    searchScope: ["missions", "clients", "documents"],
    aiSpecialist: "drone",
  },
  legal: {
    ...BASE,
    verticalId: "legal",
    contextLabel: "Legal",
    searchScope: ["clients", "documents", "cases"],
    aiSpecialist: "legal",
  },
  construction: {
    ...BASE,
    verticalId: "construction",
    contextLabel: "Строительство",
    searchScope: ["projects", "clients", "documents"],
  },
  production: {
    ...BASE,
    verticalId: "production",
    contextLabel: "Производство",
    searchScope: ["orders", "clients", "documents"],
  },
  marketplace: {
    ...BASE,
    verticalId: "marketplace",
    contextLabel: "Marketplace",
    searchScope: ["products", "clients", "campaigns"],
  },
  knowledge: {
    ...BASE,
    verticalId: "knowledge",
    contextLabel: "Знания",
    searchScope: ["knowledge", "documents"],
  },
};

export function resolveVerticalIntentConfig(
  verticalId?: string | null,
): VerticalIntentConfig {
  if (verticalId && VERTICAL_INTENT_CONFIGS[verticalId]) {
    return VERTICAL_INTENT_CONFIGS[verticalId];
  }
  return VERTICAL_INTENT_CONFIGS.owner;
}
