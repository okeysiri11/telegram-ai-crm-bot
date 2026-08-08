/**
 * Sprint 46.4 — intent classification (user never picks mode).
 */

import type { UnifiedIntentKind } from "./unifiedIntentTypes";

export function classifyUnifiedIntent(text: string): UnifiedIntentKind {
  const q = (text || "").trim().toLowerCase();
  if (!q) return "CHAT";

  if (
    /^(привет|здравствуй|добрый|hello|hi)([!.?\s]|$)/.test(q) ||
    /что\s+ты\s+умеешь|чем\s+(ты\s+)?можешь|как\s+ты\s+можешь\s+помочь|расскажи.*помочь|помощь|help/.test(
      q,
    )
  ) {
    return "CHAT";
  }

  if (/открой|перейди|откройте|open\s+/.test(q)) {
    return "NAVIGATE";
  }

  if (/запусти|workflow|автоматизац|кампани[юя]|рекламн(ую|ый)\s+кампани/.test(q)) {
    return "WORKFLOW";
  }

  if (/создай\s+(клиент|лид|контакт|документ|задач|сделк|отч|инвойс|invoice)/.test(q)) {
    return "CREATE";
  }

  if (/создай|сделай\s+мне/.test(q) && /реклам|изображ|видео|отч/.test(q)) {
    return "WORKFLOW";
  }

  if (/покажи\s+(продаж|прибыл|аналит|отч|kpi|статистик)/.test(q)) {
    return "COMMAND";
  }

  if (/найди|найти|поиск|где\s+|покажи|ищи|search/.test(q)) {
    return "SEARCH";
  }

  if (/как\s+лучше|что\s+посоветуешь|объясни|расскажи/.test(q)) {
    return "CHAT";
  }

  return "CHAT";
}

export function isChatCapabilityQuestion(text: string): boolean {
  const q = (text || "").trim().toLowerCase();
  return /умеешь|помочь|чем\s+можешь|что\s+ты|расскажи.*помощ/.test(q);
}

export const CAPABILITY_REPLY_RU =
  "Я могу помочь с:\n" +
  "• клиентами и CRM;\n" +
  "• документами;\n" +
  "• аналитикой;\n" +
  "• рекламой;\n" +
  "• AI Studio;\n" +
  "• авто;\n" +
  "• задачами;\n" +
  "• отчётами.\n\n" +
  "Например, скажите:\n" +
  "«Покажи сделки за неделю»\n" +
  "или\n" +
  "«Создай рекламу кафе».";

export const EMPTY_EXAMPLES = [
  "Покажи задачи на сегодня",
  "Найди клиента",
  "Создай отчёт",
  "Поговорить с AI",
  "Запустить рекламу",
] as const;

export const QUICK_HINTS = [
  { id: "ask", label: "Спросить AI", draft: "Расскажи, чем ты можешь помочь" },
  { id: "find", label: "Найти", draft: "Найди " },
  { id: "create", label: "Создать", draft: "Создай " },
  { id: "open", label: "Открыть", draft: "Открой " },
  { id: "run", label: "Запустить", draft: "Запусти " },
] as const;

/** Short follow-ups refine the previous SEARCH (Continuous Memory). */
export function isSearchRefine(text: string): boolean {
  const q = (text || "").trim().toLowerCase();
  if (!q || q.length > 80) return false;
  if (/найди|найти|поиск|открой|создай|запусти|расскажи|что\s+ты/.test(q)) return false;
  return /только|дешевле|дороже|ещё|еще|без\s+|с\s+дизел|бензин|до\s+\$|до\s+\d|фильтр|уточн/.test(
    q,
  )
    || (q.split(/\s+/).length <= 4 && !/^(привет|здравствуй|спасибо)/.test(q));
}

export function friendlyCategoryLabel(category: string): string {
  const map: Record<string, string> = {
    crm: "Клиенты",
    documents: "Документы",
    projects: "Проекты",
    knowledge: "Знания",
    modules: "Разделы",
    workflows: "Процессы",
    tasks: "Задачи",
    dashboards: "Панели",
    applications: "Приложения",
    ai_agents: "AI-агенты",
    commands: "Команды",
    users: "Пользователи",
    organizations: "Компании",
    erp: "ERP",
  };
  return map[category] || "Результаты";
}
