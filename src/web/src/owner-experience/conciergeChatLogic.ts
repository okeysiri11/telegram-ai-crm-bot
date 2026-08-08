/**
 * Sprint 46.3 — Concierge chat helpers (intent, sanitize, human replies).
 * No Marketing AI / Hercules jargon in client-facing strings.
 */

export type ConciergeIntent = "QUESTION" | "CHAT" | "ACTION" | "WORKFLOW";

export type ConciergeMsgKind = "chat" | "status" | "result" | "error";

export type TaskUiStatus =
  | "queued"
  | "planning"
  | "running"
  | "waiting_for_user"
  | "completed"
  | "failed"
  | "timeout";

/** Modal layout targets (mirrored in CSS). */
export const CONCIERGE_MODAL = {
  width: "min(900px, 90vw)",
  height: "min(760px, 82vh)",
  minWidthPx: 720,
  minHeightPx: 600,
  aiBubbleMax: "78%",
  userBubbleMax: "72%",
  scrollPadRightPx: 18,
} as const;

export const STATUS_COPY: Record<TaskUiStatus, string> = {
  queued: "Подготавливаю задачу…",
  planning: "Понял задачу. Готовлю план…",
  running: "⏳ Выполняю…",
  waiting_for_user: "",
  completed: "✅ Готово.",
  failed: "Не удалось выполнить задачу. Попробовать ещё раз?",
  timeout: "Задача выполняется дольше обычного.",
};

const HAND_OFF_RE =
  /передал\s+(задач[уы]|запрос)\s+.+(marketing\s*ai|через\s*консьерж)|через\s*hercules|маркетинг\s*ai|owner\s*ai|специалист\s*[«"].+[»"]/i;

export function classifyConciergeIntent(text: string): ConciergeIntent {
  const q = (text || "").trim().toLowerCase();
  if (!q) return "CHAT";

  if (
    /^(привет|здравствуй|добрый\s+(день|вечер|утро)|hello|hi)([!.?\s]|$)/.test(q) ||
    /что\s+ты\s+умеешь|чем\s+можешь|помощь|help/.test(q)
  ) {
    return "QUESTION";
  }

  if (
    /как\s+лучше|что\s+посоветуешь|подскажи|объясни|расскажи/.test(q) &&
    !/создай|запусти|сделай\s+мне|построй/.test(q)
  ) {
    return "QUESTION";
  }

  if (
    /запусти\s+реклам|создай\s+(реклам|кампани|клиент|отч|ai[- ]?задач)|построй\s+отч|workflow|автоматизац/.test(
      q,
    )
  ) {
    return "WORKFLOW";
  }

  if (
    /создай|сделай|запусти|найди\s+документ|покажи\s+сделк|построй|сгенерир|рекламн(ую|ый)\s+кампани/.test(
      q,
    )
  ) {
    return "ACTION";
  }

  if (/хочу\s+реклам|рекламировать/.test(q) && q.split(/\s+/).length <= 8) {
    return "CHAT"; // clarify first, not silent handoff
  }

  return "CHAT";
}

export function sanitizeConciergeReply(text: string): string {
  let out = (text || "").trim();
  out = out.replace(/Готово через Hercules\.?/gi, "✅ Готово.");
  out = out.replace(/^Вертикаль:\s*.+$/gim, "");
  out = out.replace(/^Цепочка:\s*.+$/gim, "");
  out = out.replace(/^Стоимость\s*≈.+$/gim, "");
  out = out.replace(/через\s*Hercules/gi, "");
  out = out.replace(/Marketing\s*AI/gi, "рекламный помощник");
  out = out.replace(/Owner\s*AI/gi, "помощник");
  out = out.replace(/\n{3,}/g, "\n\n").trim();
  if (HAND_OFF_RE.test(out) && out.length < 180) {
    return "Понял задачу. Уточните детали одним сообщением — или напишите, что именно сделать.";
  }
  return out || "Готово.";
}

export function isForbiddenHandoffReply(text: string): boolean {
  return /передал\s+задач[уы]\s+marketing\s*ai/i.test(text || "");
}

export function localConciergeReply(
  text: string,
  opts: { contextLabel: string; intent: ConciergeIntent },
): string {
  const { contextLabel, intent } = opts;
  const q = (text || "").trim().toLowerCase();

  if (/^(привет|здравствуй|добрый|hello|hi)([!.?\s]|$)/.test(q)) {
    return "Здравствуйте. Я AI Консьерж. Напишите задачу обычным языком — помогу с рекламой, клиентами, документами и отчётами.";
  }

  if (/что\s+ты\s+умеешь|чем\s+можешь|помощь|help/.test(q)) {
    return (
      "Могу помочь с рабочими задачами:\n" +
      "• реклама и тексты;\n" +
      "• клиенты и сделки;\n" +
      "• документы;\n" +
      "• отчёты;\n" +
      "• AI-задачи.\n\n" +
      "Напишите, что нужно — или нажмите быстрое действие."
    );
  }

  if (/как\s+лучше\s+реклам|как\s+рекламировать/.test(q)) {
    return (
      "Коротко: определите оффер, аудиторию и канал (Instagram / карта / рассылка), " +
      "затем сделайте один сильный креатив и тест.\n\n" +
      "Могу сразу подготовить первый вариант — напишите название и город."
    );
  }

  if (/хочу\s+реклам|рекламировать\s+кафе|реклам.*кафе/.test(q)) {
    return (
      "Понял. Могу подготовить рекламную концепцию для кафе.\n\n" +
      "Чтобы начать, мне достаточно:\n" +
      "• название;\n" +
      "• город;\n" +
      "• что хотите продвигать.\n\n" +
      "Или просто напишите:\n" +
      "«Сделай рекламу кофейни в Одессе.»"
    );
  }

  if (intent === "QUESTION" || intent === "CHAT") {
    return (
      `Я рядом. Контекст: ${contextLabel}.\n` +
      "Опишите задачу одним сообщением — или выберите быстрое действие ниже."
    );
  }

  return "Понял задачу. Сейчас выполню…";
}

export function quickActionFollowUps(action: string): string[] | null {
  if (/реклам/i.test(action)) {
    return ["Товар", "Услугу", "Компания", "Автомобиль", "Beauty", "Другое"];
  }
  return null;
}

export function promptForQuickAction(action: string): string {
  if (/реклам/i.test(action)) return "Что будем рекламировать?";
  if (/клиент/i.test(action)) return "Как зовут клиента и какой у него запрос?";
  if (/сделк/i.test(action)) return "Какие сделки показать — новые, в работе или все?";
  if (/документ/i.test(action)) return "Какой документ найти или создать?";
  if (/отчёт/i.test(action)) return "За какой период и по чему нужен отчёт?";
  if (/задач/i.test(action)) return "Сформулируйте AI-задачу одним предложением.";
  return action;
}

export function contextLabelForUser(verticalLabel: string | undefined, verticalId: string): string {
  if (!verticalId || verticalId === "owner") return "Владелец платформы";
  return verticalLabel || "Рабочее пространство";
}

export function buildSessionId(): string {
  return `concierge-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
