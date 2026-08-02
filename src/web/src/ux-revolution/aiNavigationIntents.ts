/**
 * Sprint 33.1 — Deterministic AI navigation intents (no LLM backend).
 */

export type AiNavigationIntent = {
  id: string;
  /** Phrases matched case-insensitively (EN + RU) */
  phrases: string[];
  type: "navigate" | "palette" | "create";
  route?: string;
  query?: string;
  /** If true and current mode is Simple, switch to Pro before navigate */
  requiresPro?: boolean;
  label: string;
};

export type AiNavigationMatch = AiNavigationIntent & {
  score: number;
};

export const AI_NAVIGATION_INTENTS: AiNavigationIntent[] = [
  {
    id: "create_client",
    phrases: ["create client", "new client", "создать клиента", "новый клиент", "add customer"],
    type: "create",
    route: "/crm?view=clients&action=create",
    label: "Создать клиента",
  },
  {
    id: "overdue_projects",
    phrases: [
      "show overdue projects",
      "overdue projects",
      "просроченные проекты",
      "проекты с просрочкой",
    ],
    type: "navigate",
    route: "/projects?view=overdue",
    label: "Просроченные проекты",
  },
  {
    id: "open_finance",
    phrases: ["open finance", "finance", "финансы", "открой финансы", "show finance"],
    type: "navigate",
    route: "/analytics",
    label: "Открыть Финансы",
  },
  {
    id: "find_invoice",
    phrases: ["find invoice", "invoice", "найти счёт", "счёт", "счета", "find bill"],
    type: "navigate",
    route: "/analytics?view=invoices",
    query: "invoice",
    label: "Найти счёт",
  },
  {
    id: "run_production",
    phrases: ["run production", "production", "производство", "запустить производство"],
    type: "navigate",
    route: "/erp?view=production",
    requiresPro: true,
    label: "Производство",
  },
  {
    id: "open_knowledge_graph",
    phrases: [
      "open knowledge graph",
      "knowledge graph",
      "граф знаний",
      "открой граф знаний",
      "knowledge",
    ],
    type: "navigate",
    route: "/platform-builder/knowledge",
    requiresPro: true,
    label: "Граф знаний",
  },
  {
    id: "open_crm",
    phrases: ["open crm", "crm", "открой crm", "клиенты"],
    type: "navigate",
    route: "/crm",
    label: "Открыть CRM",
  },
  {
    id: "open_dashboard",
    phrases: ["open dashboard", "dashboard", "главная", "home", "executive"],
    type: "navigate",
    route: "/dashboard",
    label: "Главная",
  },
  {
    id: "open_calendar",
    phrases: ["open calendar", "calendar", "календарь", "meetings", "встречи"],
    type: "navigate",
    route: "/calendar",
    label: "Календарь",
  },
  {
    id: "open_documents",
    phrases: ["open documents", "documents", "документы", "files"],
    type: "navigate",
    route: "/documents",
    label: "Документы",
  },
  {
    id: "open_ai",
    phrases: ["open ai", "ai assistant", "ai-агент", "ассистент", "агенты"],
    type: "navigate",
    route: "/ai-agents",
    label: "AI-Ассистент",
  },
  {
    id: "open_settings",
    phrases: ["open settings", "settings", "настройки"],
    type: "navigate",
    route: "/settings",
    label: "Настройки",
  },
  {
    id: "open_marketplace",
    phrases: ["open marketplace", "marketplace", "маркетплейс"],
    type: "navigate",
    route: "/marketplace",
    requiresPro: true,
    label: "Маркетплейс",
  },
  {
    id: "open_security",
    phrases: ["open security", "security", "безопасность", "security center"],
    type: "navigate",
    route: "/identity/security",
    requiresPro: true,
    label: "Безопасность",
  },
  {
    id: "ask_ai",
    phrases: ["ask ai", "спроси ai", "помощь ai", "help"],
    type: "palette",
    label: "Спросить AI",
  },
];

export function matchAiNavigationIntent(query: string): AiNavigationMatch | null {
  const q = query.trim().toLowerCase();
  if (!q || q.length < 2) return null;

  let best: AiNavigationMatch | null = null;
  for (const intent of AI_NAVIGATION_INTENTS) {
    for (const phrase of intent.phrases) {
      const p = phrase.toLowerCase();
      let score = 0;
      if (q === p) score = 100;
      else if (q.startsWith(p) || p.startsWith(q)) score = 80;
      else if (q.includes(p) || p.includes(q)) score = 60;
      else {
        const tokens = q.split(/\s+/);
        const hit = tokens.filter((t) => p.includes(t) && t.length > 2).length;
        if (hit) score = 40 + hit * 5;
      }
      if (score > 0 && (!best || score > best.score)) {
        best = { ...intent, score };
      }
    }
  }
  return best && best.score >= 40 ? best : null;
}
