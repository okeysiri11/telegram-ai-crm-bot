/**
 * Sprint 42.3 — Auto-specific AI intents (deterministic, no LLM).
 */

import {
  AI_NAVIGATION_INTENTS,
  matchAiNavigationIntent,
  type AiNavigationIntent,
  type AiNavigationMatch,
} from "@/ux-revolution/aiNavigationIntents";

export const AUTO_AI_INTENTS: AiNavigationIntent[] = [
  {
    id: "auto_add_vehicle",
    phrases: [
      "добавь автомобиль",
      "добавить автомобиль",
      "новый автомобиль",
      "add car",
      "add vehicle",
      "создай авто",
    ],
    type: "create",
    route: "/workspace/auto?action=vehicle",
    label: "Добавить автомобиль",
  },
  {
    id: "auto_find_client",
    phrases: ["найди клиента", "найти клиента", "клиент", "find client", "find customer"],
    type: "navigate",
    route: "/workspace/auto?view=clients",
    label: "Найти клиента",
  },
  {
    id: "auto_show_sales",
    phrases: ["покажи продажи", "продажи", "show sales", "sales"],
    type: "navigate",
    route: "/workspace/auto?view=sales",
    label: "Показать продажи",
  },
  {
    id: "auto_import_vin",
    phrases: ["импортируй vin", "импорт vin", "import vin", "vin"],
    type: "create",
    route: "/workspace/auto?view=import&action=vin",
    label: "Импортировать VIN",
  },
  {
    id: "auto_create_contract",
    phrases: ["создай договор", "создать договор", "договор", "create contract"],
    type: "create",
    route: "/workspace/auto?view=sales&action=contract",
    label: "Создать договор",
  },
  {
    id: "auto_cars",
    phrases: ["автомобили", "каталог", "cars", "vehicles"],
    type: "navigate",
    route: "/workspace/auto?view=cars",
    label: "Автомобили",
  },
  {
    id: "auto_warehouse",
    phrases: ["склад", "warehouse", "сток"],
    type: "navigate",
    route: "/workspace/auto?view=warehouse",
    label: "Склад",
  },
  {
    id: "auto_fix_photos",
    phrases: ["фото", "без фото", "добавить фото", "photos", "fix photos"],
    type: "navigate",
    route: "/workspace/auto?view=cars&action=photos",
    label: "Добавить фотографии",
  },
];

export const AUTO_AI_CHIPS = [
  { label: "Добавь автомобиль", text: "Добавь автомобиль" },
  { label: "Найди клиента", text: "Найди клиента" },
  { label: "Покажи продажи", text: "Покажи продажи" },
  { label: "Импортируй VIN", text: "Импортируй VIN" },
  { label: "Создай договор", text: "Создай договор" },
] as const;

/** Prefer Auto intents, then global navigation intents. */
export function matchAutoAiIntent(query: string): AiNavigationMatch | null {
  const q = query.trim().toLowerCase();
  if (!q || q.length < 2) return null;

  let best: AiNavigationMatch | null = null;
  for (const intent of [...AUTO_AI_INTENTS, ...AI_NAVIGATION_INTENTS]) {
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
  return best && best.score >= 40 ? best : matchAiNavigationIntent(query);
}
