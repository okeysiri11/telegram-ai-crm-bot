export const CP_TYPES: Record<string, string> = {
  farmer: "Фермер / хозяйство",
  farm: "Фермер / хозяйство",
  producer: "Производитель",
  agro_company: "Агрокомпания",
  supplier: "Поставщик",
  buyer: "Покупатель",
  exporter: "Экспортёр",
  importer: "Импортёр",
  trader: "Трейдер",
  elevator: "Элеватор",
  warehouse: "Склад",
  processor: "Переработчик",
  plant: "Завод",
  carrier: "Перевозчик",
  forwarder: "Экспедитор",
  port: "Порт / терминал",
  bank: "Банк",
  insurance: "Страховая компания",
  broker: "Брокер",
  counterparty: "Контрагент",
  other: "Другое",
};

export const CP_STATUSES: Record<string, string> = {
  lead: "Новый",
  new: "Новый",
  active: "Активный",
  negotiation: "Переговоры",
  review: "На проверке",
  on_hold: "Приостановлен",
  risk: "Проблемный",
  problem: "Проблемный",
  blocked: "Чёрный список",
  blacklist: "Чёрный список",
  archived: "Архив",
};

export const DEAL_STATUSES: Record<string, string> = {
  draft: "Новая",
  negotiation: "Переговоры",
  approved: "Согласование",
  awaiting_contract: "Ожидает договор",
  contracted: "Договор подписан",
  awaiting_payment: "Ожидает оплату",
  paid_partly: "Оплачено частично",
  paid: "Оплачено",
  in_delivery: "В поставке",
  delivered: "Получено / передано",
  closed: "Закрыта",
  problem: "Проблема",
  cancelled: "Отменена",
};

export const DEAL_PIPELINE: { id: string; label: string; statuses: string[] }[] = [
  { id: "new", label: "Новая", statuses: ["draft"] },
  { id: "negotiation", label: "Переговоры", statuses: ["negotiation"] },
  { id: "approval", label: "Согласование", statuses: ["approved"] },
  { id: "contract", label: "Договор", statuses: ["awaiting_contract", "contracted"] },
  { id: "payment", label: "Оплата", statuses: ["awaiting_payment", "paid_partly", "paid"] },
  { id: "delivery", label: "Поставка", statuses: ["in_delivery", "delivered"] },
  { id: "closed", label: "Закрыта", statuses: ["closed"] },
  { id: "problem", label: "Проблема", statuses: ["cancelled", "risk", "problem", "blocked"] },
];

export function dealPipelineId(status: string): string {
  const st = String(status || "").toLowerCase();
  return DEAL_PIPELINE.find((p) => p.statuses.includes(st))?.id || "new";
}

export const DOC_TYPES: Record<string, string> = {
  contract: "Договор",
  invoice: "Счёт",
  specification: "Спецификация",
  act: "Акт",
  certificate: "Сертификат",
  quality_certificate: "Сертификат качества",
  phytosanitary: "Фитосанитарный документ",
  cmr: "CMR (международная накладная)",
  ttn: "ТТН",
  customs: "Таможенный документ",
  tax: "Налоговый документ",
  bank: "Банковский документ",
  insurance: "Страховка",
  photo: "Фото",
  tech_passport: "Техпаспорт",
  inspection: "Техосмотр",
  permit: "Разрешение",
  driver_license: "Водительское удостоверение",
  passport: "Паспорт / ID",
  id_document: "Документ личности",
  medical: "Медсправка",
  weight_ticket: "Весовая",
  other: "Другое",
};

export const ENTITY_TYPES: Record<string, string> = {
  counterparty: "Контрагент",
  contact: "Контакт",
  deal: "Сделка",
  contract: "Договор",
  document: "Документ",
  invoice: "Счёт",
  calculation: "Расчёт",
  payment: "Оплата",
  shipment: "Поставка",
  warehouse: "Склад",
  task: "Задача",
  crop: "Культура",
  calendar: "Событие",
  carrier: "Перевозчик",
  vehicle: "Автомобиль",
  trailer: "Прицеп",
  driver: "Водитель",
  trip: "Рейс",
  market: "Рынок",
  market_price: "Цена",
  inventory_lot: "Партия",
  storage_unit: "Секция склада",
  agro_operation: "Операция",
  weighing: "Взвешивание",
  quality_test: "Анализ качества",
  truck_run: "Рейс машины",
};

export const ROLE_RU: Record<string, string> = {
  agro_director: "Директор",
  agro_accountant: "Бухгалтер",
  agro_manager: "Менеджер",
  agro_observer: "Наблюдатель",
  agro_viewer: "Наблюдатель",
  agro_logistics: "Логист",
  agro_warehouse: "Склад",
  agro_quality: "Качество",
  agro_agronomist: "Агроном",
  agro_mechanic: "Механик",
  platform_owner: "Владелец платформы",
};

export const GENERIC_STATUS: Record<string, string> = {
  ...CP_STATUSES,
  ...DEAL_STATUSES,
  new: "Новая",
  planned: "Запланировано",
  expected: "Ожидается",
  scheduled: "Назначено",
  done: "Выполнено",
  in_transit: "В пути",
  uploaded: "Загружен",
  watch: "Наблюдение",
  viewed: "Просмотрено",
  unpaid: "Не оплачен",
  overdue: "Просрочено",
  issued: "Выставлен",
  archived: "Архив",
  cancelled: "Отменена",
  free: "Свободен",
  assigned: "Назначен",
  in_trip: "В рейсе",
  repair: "Ремонт",
  inactive: "Неактивен",
  loading: "Погрузка",
  unloading: "Разгрузка",
};

export const FRESHNESS_RU: Record<string, string> = {
  LIVE: "Актуально",
  CONNECTED: "Подключён",
  DEGRADED: "Частично доступен",
  DELAYED: "Задержка обновления",
  STALE: "Устарело",
  NOT_CONFIGURED: "Источник не подключён",
  UNAVAILABLE: "Источник недоступен",
  ERROR: "Ошибка источника",
  BLOCKED: "Доступ запрещён",
  PARTIAL: "Частично доступен",
  REQUIRES_CONFIGURATION: "Требуется настройка",
  NEEDS_KEY: "Нужен API-ключ",
  NEEDS_LICENSE: "Нужна лицензия",
  METADATA_ONLY: "Только метаданные",
  OPTIONAL_NOT_CONFIGURED: "Опциональный, не настроен",
  FAILED: "Ошибка источника",
};

export const HEALTH_HEX: Record<string, string> = {
  green: "#16a34a",
  yellow: "#ca8a04",
  orange: "#ea580c",
  red: "#dc2626",
  gray: "#6b7280",
};

export const HEALTH_STATE_COLOR: Record<string, string> = {
  CONNECTED: "green",
  PARTIAL: "yellow",
  STALE: "yellow",
  NEEDS_KEY: "orange",
  NEEDS_LICENSE: "orange",
  BLOCKED: "red",
  FAILED: "red",
  METADATA_ONLY: "gray",
  OPTIONAL_NOT_CONFIGURED: "gray",
  REQUIRES_CONFIGURATION: "gray",
  NOT_CONFIGURED: "gray",
};

export const GAP_SEVERITY_RU: Record<string, string> = {
  CRITICAL: "Критичный",
  IMPORTANT: "Важный",
  OPTIONAL: "Опциональный",
};

export const RISK_LEVEL_RU: Record<string, string> = {
  LOW: "Низкий",
  MEDIUM: "Средний",
  HIGH: "Высокий",
  CRITICAL: "Критичный",
};

export const CONFIDENCE_RU: Record<string, string> = {
  low: "Низкая",
  medium: "Средняя",
  high: "Высокая",
};

export const BIAS_RU: Record<string, string> = {
  WATCH: "Наблюдение",
  NEUTRAL: "Нейтрально",
  POSITIVE: "Позитивный",
  NEGATIVE: "Негативный",
  RISK: "Риск",
  OPPORTUNITY: "Возможность",
};

export const SIDE_RU: Record<string, string> = {
  buy: "Закупка",
  sell: "Продажа",
};

export const DIRECTION_RU: Record<string, string> = {
  in: "Входящая (нам должны)",
  out: "Исходящая (мы должны)",
};

export const EVENT_TYPES: Record<string, string> = {
  meeting: "Встреча",
  payment: "Платёж",
  shipment: "Поставка",
  contract: "Договор",
  task: "Задача",
};

export const QUALITY_RU: Record<string, string> = {
  moisture: "влажность",
  protein: "протеин",
  gluten: "клейковина",
  foreign_matter: "сорность",
  oil_content: "масличность",
  test_weight: "натура",
};

export function ru(map: Record<string, string>, value: string | undefined | null): string {
  if (!value) return "—";
  return map[value] || map[value.toLowerCase()] || value;
}

export function ruStatus(value: string | undefined | null): string {
  return ru(GENERIC_STATUS, value);
}

export function typesRu(types: unknown): string {
  if (Array.isArray(types)) return types.map((t) => ru(CP_TYPES, String(t))).join(", ");
  if (typeof types === "string") {
    return types
      .split(",")
      .map((t) => ru(CP_TYPES, t.trim()))
      .join(", ");
  }
  return "—";
}

export function qualityRu(attrs: unknown): string {
  if (!attrs || typeof attrs !== "object") return "—";
  const parts = Object.entries(attrs as Record<string, unknown>)
    .filter(([, v]) => v != null && String(v).trim())
    .map(([k, v]) => `${QUALITY_RU[k] || k}: ${String(v)}`);
  return parts.join(", ") || "—";
}
