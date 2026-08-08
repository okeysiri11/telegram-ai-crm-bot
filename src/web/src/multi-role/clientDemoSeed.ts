/**
 * Sprint 42.1 — client demo seed (CRM/docs/analytics/AI/notifications).
 */

import type { DemoUserDef } from "./demoUsers";
import { wsKey } from "./workspaceSlot";
import { useNotificationStore } from "@/notifications/notificationStore";

export const CLIENT_DEMO_SEED_KEY = "ewp_client_demo_seed_v1";

export type ClientDemoSeed = {
  company: string;
  clients: Array<{ id: string; name: string; status: string }>;
  documents: Array<{ id: string; title: string; kind: string }>;
  analytics: Array<{ label: string; value: string }>;
  aiMessages: Array<{ id: string; text: string }>;
  seededAt: string;
};

export function seedClientDemoData(user: DemoUserDef): ClientDemoSeed {
  const seed: ClientDemoSeed = {
    company: user.company,
    clients: [
      { id: "c1", name: "Acme Travel", status: "active" },
      { id: "c2", name: "Nordic Tours", status: "lead" },
      { id: "c3", name: "City Breaks LLC", status: "active" },
    ],
    documents: [
      { id: "d1", title: "Договор обслуживания.pdf", kind: "contract" },
      { id: "d2", title: "Прайс B2B.xlsx", kind: "sheet" },
      { id: "d3", title: "Онбординг.docx", kind: "guide" },
    ],
    analytics: [
      { label: "Лиды (7д)", value: "12" },
      { label: "Сделки", value: "5" },
      { label: "Конверсия", value: "18%" },
    ],
    aiMessages: [
      { id: "a1", text: "Доброе утро. Сегодня 5 новых лидов и 2 задачи." },
      { id: "a2", text: "Рекомендую открыть CRM и квалифицировать новые лиды." },
    ],
    seededAt: new Date().toISOString(),
  };

  try {
    localStorage.setItem(wsKey(CLIENT_DEMO_SEED_KEY), JSON.stringify(seed));
  } catch {
    /* ignore */
  }

  try {
    const store = useNotificationStore.getState();
    store.push({
      kind: "info",
      title: "Демо: новый лид",
      body: "Корпоративные билеты — ожидает ответа",
    });
    store.push({
      kind: "task",
      title: "Демо: документ",
      body: "Договор загружен в Documents",
    });
    store.push({
      kind: "ai",
      title: "Демо: AI-сводка",
      body: "Утренние приоритеты готовы",
    });
  } catch {
    /* ignore */
  }

  return seed;
}

export function readClientDemoSeed(): ClientDemoSeed | null {
  try {
    const raw = localStorage.getItem(wsKey(CLIENT_DEMO_SEED_KEY));
    if (!raw) return null;
    return JSON.parse(raw) as ClientDemoSeed;
  } catch {
    return null;
  }
}
