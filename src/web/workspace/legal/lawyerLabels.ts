export const STATUS_RU: Record<string, string> = {
  open: "Открыто",
  closed: "Закрыто",
  pending: "Ожидает",
  draft: "Черновик",
  active: "Активен",
  approved: "Согласовано",
  scheduled: "Назначено",
  completed: "Завершено",
  cancelled: "Отменено",
  canceled: "Отменено",
  uploaded: "Загружен",
  local: "Локально",
  synced: "Синхронизировано",
  needs_config: "Требуется настройка",
  needs_oauth: "Требуется авторизация Google",
  connected: "Подключено",
  coming_soon: "Скоро",
  error: "Ошибка",
  UNAVAILABLE: "Источник временно недоступен",
  REQUIRES_CONFIGURATION: "Требуется настройка",
  MANUAL: "Ручной режим",
  unavailable: "Источник временно недоступен",
  disabled: "Отключён",
  viewed: "Просмотрено",
  needs_action: "Требует действия",
  hearing: "Заседание",
  meeting: "Встреча с клиентом",
  consultation: "Консультация",
  deadline: "Срок",
  task: "Задача",
  contract_end: "Окончание договора",
  internal: "Внутренняя встреча",
  other: "Другое",
  criminal: "Уголовное",
  civil: "Гражданское",
  commercial: "Коммерческое",
  high: "Высокий",
  normal: "Обычный",
  low: "Низкий",
  critical: "Критический",
  person: "Физическое лицо",
  company: "Юридическое лицо",
  new: "Новая",
  in_progress: "В работе",
  waiting: "Ожидает",
  done: "Выполнена",
  overdue: "Просрочена",
  in_person: "Очно",
  online: "Онлайн",
  services: "Услуги",
};

export function ruStatus(value: string | null | undefined): string {
  if (!value) return "—";
  return STATUS_RU[String(value)] || String(value);
}

export const EVENT_TYPES = [
  { id: "hearing", label: "Заседание" },
  { id: "meeting", label: "Встреча с клиентом" },
  { id: "consultation", label: "Консультация" },
  { id: "deadline", label: "Срок" },
  { id: "task", label: "Задача" },
  { id: "contract_end", label: "Окончание договора" },
  { id: "internal", label: "Внутренняя встреча" },
  { id: "other", label: "Другое" },
];

export const REMINDERS = [
  { minutes: 0, label: "Нет" },
  { minutes: 15, label: "За 15 минут" },
  { minutes: 30, label: "За 30 минут" },
  { minutes: 60, label: "За 1 час" },
  { minutes: 1440, label: "За 1 день" },
];

export const TASK_STATUSES = [
  { id: "new", label: "Новая" },
  { id: "in_progress", label: "В работе" },
  { id: "waiting", label: "Ожидает" },
  { id: "done", label: "Выполнена" },
  { id: "overdue", label: "Просрочена" },
  { id: "cancelled", label: "Отменена" },
];

export const TASK_PRIORITIES = [
  { id: "low", label: "Низкий" },
  { id: "normal", label: "Обычный" },
  { id: "high", label: "Высокий" },
  { id: "critical", label: "Критический" },
];

export const TASK_VIEWS = [
  { id: "all", label: "Все" },
  { id: "today", label: "Сегодня" },
  { id: "week", label: "На этой неделе" },
  { id: "overdue", label: "Просроченные" },
  { id: "done", label: "Выполненные" },
];
