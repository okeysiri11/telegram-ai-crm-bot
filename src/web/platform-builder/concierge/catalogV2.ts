/**
 * Sprint 42.4 — AI Concierge Builder 2.0 catalog (RU-first, 7 steps).
 */

export const CONCIERGE_V2_STEPS = [
  "Имя и образ",
  "Роль",
  "Стиль общения",
  "Навыки",
  "Модули",
  "Права",
  "Тестовый диалог",
] as const;

export const V2_AVATARS = [
  { id: "avatar_exec", name: "Деловой", emoji: "🧑‍💼" },
  { id: "avatar_guide", name: "Навигатор", emoji: "🧭" },
  { id: "avatar_spark", name: "Искра", emoji: "✨" },
  { id: "avatar_shield", name: "Надёжный", emoji: "🛡️" },
];

export const V2_VOICES = [
  { id: "warm", name: "Тёплый" },
  { id: "clear", name: "Чёткий" },
  { id: "confident", name: "Уверенный" },
  { id: "soft", name: "Мягкий" },
];

export const V2_LANGUAGES = [
  { id: "ru", name: "Русский" },
  { id: "en", name: "Английский" },
  { id: "uk", name: "Українська" },
];

export const V2_ROLES = [
  { id: "concierge", name: "Консьерж" },
  { id: "manager", name: "Менеджер" },
  { id: "lawyer", name: "Юрист" },
  { id: "financier", name: "Финансист" },
  { id: "analyst", name: "Аналитик" },
  { id: "assistant", name: "Помощник" },
  { id: "consultant", name: "Консультант" },
  { id: "custom", name: "Свой вариант" },
];

export const V2_STYLES = [
  { id: "friendly", name: "Дружелюбный", sample: "Здравствуйте! Чем могу помочь сегодня?" },
  { id: "business", name: "Деловой", sample: "Добрый день. Готов к приоритетам и решениям." },
  { id: "mentor", name: "Наставник", sample: "Давайте разберём по шагам: цель → действие → результат." },
  { id: "brief", name: "Краткий", sample: "Три пункта. Один следующий шаг." },
  { id: "detailed", name: "Подробный", sample: "Ниже полный разбор ситуации и варианты." },
  { id: "to_the_point", name: "Только по делу", sample: "Факт. Риск. Действие." },
  { id: "calm", name: "Спокойный", sample: "Спокойно пройдём по списку задач." },
];

export const V2_SKILLS = [
  { id: "crm", name: "CRM" },
  { id: "documents", name: "Документы" },
  { id: "telegram", name: "Telegram" },
  { id: "whatsapp", name: "WhatsApp" },
  { id: "email", name: "Email" },
  { id: "calendar", name: "Календарь" },
  { id: "tasks", name: "Задачи" },
  { id: "finance", name: "Финансы" },
  { id: "search", name: "Поиск" },
  { id: "reports", name: "Отчёты" },
];

export const V2_MODULES = [
  { id: "auto", name: "Авто" },
  { id: "crypto", name: "Crypto OTC" },
  { id: "drone", name: "БПЛА" },
  { id: "agro", name: "Агро" },
  { id: "travel", name: "Туризм" },
  { id: "erp", name: "ERP" },
  { id: "crm", name: "CRM" },
  { id: "manufacturing", name: "Производство" },
  { id: "construction", name: "Строительство" },
  { id: "legal", name: "Юридический отдел" },
];

export const V2_PERMISSIONS = [
  { id: "read", name: "Чтение" },
  { id: "create", name: "Создание" },
  { id: "update", name: "Изменение" },
  { id: "delete", name: "Удаление" },
  { id: "run_workflows", name: "Запуск сценариев" },
  { id: "act_as_user", name: "Работа от имени пользователя" },
];

export type ConciergeV2Draft = {
  name: string;
  avatar: string;
  voice: string;
  language: string;
  greeting: string;
  role: string | null;
  roleCustom: string;
  style: string;
  skills: string[];
  modules: string[];
  permissions: string[];
};

export function emptyConciergeV2(): ConciergeV2Draft {
  return {
    name: "",
    avatar: "avatar_exec",
    voice: "clear",
    language: "ru",
    greeting: "Здравствуйте! Я ваш AI Консьерж. Чем помочь?",
    role: "concierge",
    roleCustom: "",
    style: "friendly",
    skills: ["crm", "documents", "calendar", "tasks"],
    modules: ["crm"],
    permissions: ["read", "create"],
  };
}

/** Map V2 draft → legacy API payload fields. */
export function v2ToApiDraft(d: ConciergeV2Draft) {
  const roleMap: Record<string, string> = {
    concierge: "business_concierge",
    manager: "operations_manager",
    lawyer: "custom",
    financier: "custom",
    analyst: "custom",
    assistant: "executive_assistant",
    consultant: "business_advisor",
    custom: "custom",
  };
  const styleMap: Record<string, string> = {
    friendly: "friendly",
    business: "business_executive",
    mentor: "mentor",
    brief: "direct",
    detailed: "professional",
    to_the_point: "without_formalities",
    calm: "calm",
  };
  const accessFromSkills = d.skills.filter((s) =>
    ["crm", "documents", "calendar", "tasks", "finance"].includes(s),
  );
  return {
    name: d.name,
    avatar: d.avatar,
    gender: "neutral" as const,
    voice_profile: d.voice,
    communication_style: styleMap[d.style] || "professional",
    role: roleMap[d.role || "concierge"] || "business_concierge",
    role_custom: d.role === "custom" ? d.roleCustom : d.role || "",
    organization_access: [...new Set([...accessFromSkills, ...d.modules.filter((m) => ["crm", "erp"].includes(m))])],
    orchestration: ["delegate_tasks", "recommend_specialists"],
    proactive: ["morning_briefing", "important_reminders"],
    owner_relationship: "balanced",
    recommendations: ["recommend_workflows", "recommend_knowledge"],
    group_ai_invite_roles: ["Lawyer", "Finance", "Аналитика"],
    enable_ai_team_center: true,
    language: d.language,
    greeting: d.greeting,
    skills: d.skills,
    modules: d.modules,
    permissions: d.permissions,
  };
}

export function previewReply(draft: ConciergeV2Draft, userMessage: string): string {
  const style = V2_STYLES.find((s) => s.id === draft.style);
  const role = V2_ROLES.find((r) => r.id === draft.role);
  const name = draft.name.trim() || "AI Консьерж";
  const q = userMessage.trim() || "…";
  return `${name} (${role?.name || "Консьерж"}): ${style?.sample || ""} Ответ на «${q}»: я учту навыки ${draft.skills.slice(0, 3).map((id) => V2_SKILLS.find((s) => s.id === id)?.name || id).join(", ") || "базовые"} и модули ${draft.modules.slice(0, 2).map((id) => V2_MODULES.find((m) => m.id === id)?.name || id).join(", ") || "платформы"}.`;
}
