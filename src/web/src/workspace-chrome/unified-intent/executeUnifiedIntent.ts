/**
 * Sprint 46.4 — execute classified intents via existing Command Center / search / ACC.
 */

import { interpretAiIntent } from "@/runtime/commandRuntime/aiIntentRouter";
import { commandRuntime } from "@/runtime/commandRuntime/commandRuntime";
import { searchProvider } from "../../../navigation/managers/searchProvider";
import { COMMAND_CATALOG } from "../../../command-center/managers/quickActions";
import { telemetry } from "@/integrations/telemetry";
import {
  CAPABILITY_REPLY_RU,
  classifyUnifiedIntent,
  friendlyCategoryLabel,
  isChatCapabilityQuestion,
  isSearchRefine,
} from "./unifiedIntentRouter";
import { useUnifiedIntentStore } from "./unifiedIntentStore";
import type { IntentInteraction, UnifiedIntentKind } from "./unifiedIntentTypes";
import { sanitizeConciergeReply } from "@/owner-experience/conciergeChatLogic";

export type ExecuteCtx = {
  verticalId?: string;
  navigate: (path: string) => void;
  openAiChat?: () => void;
  sessionId?: string;
};

async function callAiCommand(text: string, sessionId?: string): Promise<string> {
  const res = await fetch("/management/v1/ai-command/chat", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      channel: "web",
      session_id: sessionId || `intent-${Date.now().toString(36)}`,
      role: "owner",
      max_steps: 2,
    }),
  });
  const json = await res.json().catch(() => ({}));
  const data = json?.data || json || {};
  const raw =
    data.reply_ru || json?.reply_ru || (res.ok ? "Готово." : "Не удалось выполнить задачу.");
  return sanitizeConciergeReply(String(raw));
}

function findNavigateRoute(text: string): { route?: string; label?: string; commandId?: string } {
  const mapped = interpretAiIntent(text);
  if (mapped.ok && mapped.route) {
    return { route: mapped.route, label: mapped.label, commandId: mapped.commandId };
  }
  const q = text.toLowerCase();
  const hit = COMMAND_CATALOG.find((c) => {
    const hay = `${c.label} ${c.action} ${(c.keywords || []).join(" ")}`.toLowerCase();
    if (q.includes("crm") && hay.includes("crm")) return true;
    return q.split(/\s+/).some((w) => w.length > 2 && hay.includes(w) && Boolean(c.route));
  });
  if (hit?.route) return { route: hit.route, label: hit.label, commandId: hit.id };
  return {};
}

function resolveSearchQuery(text: string): string {
  const store = useUnifiedIntentStore.getState();
  if (!isSearchRefine(text)) return text;
  const prev = store.items.find((i) => i.intent === "SEARCH" && i.status === "completed");
  if (!prev?.text) return text;
  return `${prev.text}. ${text}`;
}

function pluralRu(n: number): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return "";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return "а";
  return "ов";
}

/**
 * Create interaction + run. Caller must clear the input *before* awaiting this.
 */
export async function executeUnifiedIntent(
  text: string,
  ctx: ExecuteCtx,
): Promise<IntentInteraction> {
  const store = useUnifiedIntentStore.getState();
  let intent = classifyUnifiedIntent(text);
  if (
    isSearchRefine(text) &&
    store.items.some((i) => i.intent === "SEARCH" && i.status === "completed")
  ) {
    intent = "SEARCH";
  }
  const item = store.create(text, intent, ctx.verticalId);
  const started = Date.now();

  store.setStatus(item.id, "routing", { progressLabel: "Принял задачу" });
  void telemetry.userActivity(`unified_intent:${intent}`);

  try {
    if (intent === "CHAT") {
      store.setStatus(item.id, "running", { progressLabel: "Готовлю ответ…" });
      if (isChatCapabilityQuestion(text)) {
        store.setStatus(item.id, "completed", {
          reply: CAPABILITY_REPLY_RU,
          progressLabel: undefined,
          debug: { latencyMs: Date.now() - started },
        });
        return useUnifiedIntentStore.getState().items.find((i) => i.id === item.id)!;
      }
      const reply = await callAiCommand(text, ctx.sessionId);
      store.setStatus(item.id, "completed", {
        reply,
        progressLabel: undefined,
        debug: { latencyMs: Date.now() - started },
      });
      return useUnifiedIntentStore.getState().items.find((i) => i.id === item.id)!;
    }

    if (intent === "NAVIGATE") {
      store.setStatus(item.id, "running", { progressLabel: "Открываю…" });
      const nav = findNavigateRoute(text);
      if (nav.route) {
        commandRuntime.bindNavigator(ctx.navigate);
        ctx.navigate(nav.route);
        store.setStatus(item.id, "completed", {
          reply: `Открываю: ${nav.label || nav.route}`,
          resultPath: nav.route,
          progressLabel: undefined,
          debug: {
            route: nav.route,
            commandId: nav.commandId,
            latencyMs: Date.now() - started,
          },
        });
      } else {
        store.setStatus(item.id, "failed", {
          error: "Не удалось определить раздел.",
          reply: "Не нашёл раздел. Уточните: например «Открой CRM».",
          progressLabel: undefined,
        });
      }
      return useUnifiedIntentStore.getState().items.find((i) => i.id === item.id)!;
    }

    if (intent === "SEARCH") {
      store.setStatus(item.id, "running", { progressLabel: "Ищу…" });
      const query = resolveSearchQuery(text);
      const allHits = searchProvider.search(query).slice(0, 40);
      const groups = new Map<string, number>();
      for (const h of allHits) {
        groups.set(h.category, (groups.get(h.category) || 0) + 1);
      }
      const summaryParts = [...groups.entries()]
        .map(([cat, n]) => `${friendlyCategoryLabel(cat)} — ${n}`)
        .join(", ");
      const count = allHits.length;
      const path = `/search?q=${encodeURIComponent(query)}`;
      ctx.navigate(path);
      store.setStatus(item.id, "completed", {
        reply: count
          ? `Нашёл ${count} результат${pluralRu(count)}.\n${summaryParts}`
          : "По запросу пока ничего не нашёл. Попробуйте уточнить.",
        resultPath: path,
        resultCount: count,
        progressLabel: undefined,
        hits: allHits.slice(0, 12).map((h) => ({
          id: h.id,
          title: h.title,
          path: h.path,
          category: h.category,
          categoryLabel: friendlyCategoryLabel(h.category),
        })),
        debug: { route: path, latencyMs: Date.now() - started },
      });
      return useUnifiedIntentStore.getState().items.find((i) => i.id === item.id)!;
    }

    // CREATE / COMMAND / WORKFLOW → AI Command Center
    store.setStatus(item.id, "running", {
      progressLabel:
        intent === "WORKFLOW"
          ? "Запускаю сценарий…"
          : intent === "CREATE"
            ? "Создаю…"
            : "Анализирую…",
    });
    const reply = await callAiCommand(text, ctx.sessionId);
    store.setStatus(item.id, "completed", {
      reply,
      progressLabel: undefined,
      debug: { latencyMs: Date.now() - started, commandId: intent },
    });
    return useUnifiedIntentStore.getState().items.find((i) => i.id === item.id)!;
  } catch {
    store.setStatus(item.id, "failed", {
      error: "Не удалось выполнить задачу.",
      reply: "Не удалось выполнить задачу.",
      progressLabel: undefined,
      debug: { latencyMs: Date.now() - started },
    });
    return useUnifiedIntentStore.getState().items.find((i) => i.id === item.id)!;
  }
}

export function intentKindLabel(kind: UnifiedIntentKind): string {
  const map: Record<UnifiedIntentKind, string> = {
    CHAT: "Диалог",
    SEARCH: "Поиск",
    COMMAND: "Команда",
    CREATE: "Создание",
    NAVIGATE: "Переход",
    WORKFLOW: "Сценарий",
  };
  return map[kind];
}
