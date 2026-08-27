export const RECRUITING_NAV = [
  { id: "home", label: "Главная" },
  { id: "leads", label: "Лиды" },
  { id: "candidates", label: "Кандидаты" },
  { id: "vacancies", label: "Вакансии" },
  { id: "pipeline", label: "Воронка" },
  { id: "campaigns", label: "Кампании" },
  { id: "tasks", label: "Задачи" },
  { id: "comms", label: "Коммуникации" },
  { id: "activity", label: "Активность" },
  { id: "analytics", label: "Аналитика" },
] as const;

export const PIPELINE_STAGES = ["NEW", "QUALIFIED", "INTERVIEW", "APPROVED", "HIRED", "REJECTED"] as const;

export const PIPELINE_LABELS: Record<string, string> = {
  NEW: "Новые",
  QUALIFIED: "Квалификация",
  INTERVIEW: "Интервью",
  APPROVED: "Одобрены",
  HIRED: "Наняты",
  REJECTED: "Отказ",
};

export const TASK_TEMPLATES = [
  "Позвонить",
  "Написать",
  "Провести интервью",
  "Проверить анкету",
  "Отправить приглашение",
] as const;

export const COMM_CHANNELS = ["PHONE", "TELEGRAM", "WHATSAPP", "EMAIL", "MANUAL"] as const;

export const COMM_LABELS: Record<string, string> = {
  PHONE: "Телефон",
  TELEGRAM: "Telegram",
  WHATSAPP: "WhatsApp",
  EMAIL: "Email",
  MANUAL: "Вручную",
};

export function ruLeadStatus(status: string): string {
  const map: Record<string, string> = {
    new: "Новый",
    qualified: "Квалифицирован",
    converted: "Кандидат",
    lost: "Потерян",
  };
  return map[status] || status || "—";
}

export function mapUiRoleToRecruiting(roleId: string): string {
  const raw = (roleId || "").toLowerCase();
  if (raw.includes("platform_owner") || raw === "owner") return "platform_owner";
  if (raw.includes("observer") || raw.includes("viewer") || raw.includes("наблюдатель")) return "observer";
  if (raw.includes("manager") || raw.includes("директор") || raw.includes("partner")) return "hiring_manager";
  return "recruiter";
}
