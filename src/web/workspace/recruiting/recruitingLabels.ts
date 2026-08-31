export const RECRUITING_NAV = [
  { id: "home", label: "Главная", href: "/workspace/recruiting" },
  { id: "projects", label: "Проекты", href: "/workspace/recruiting/projects" },
  { id: "leads", label: "Лиды", href: "/workspace/recruiting?view=leads" },
  { id: "candidates", label: "Кандидаты", href: "/workspace/recruiting?view=candidates" },
  { id: "vacancies", label: "Вакансии", href: "/workspace/recruiting?view=vacancies" },
  { id: "pipeline", label: "Воронка", href: "/workspace/recruiting?view=pipeline" },
  { id: "campaigns", label: "Кампании", href: "/workspace/recruiting?view=campaigns" },
  { id: "ads", label: "Реклама", href: "/workspace/recruiting/ads" },
  { id: "integrations", label: "Интеграции", href: "/workspace/recruiting/integrations" },
  { id: "tasks", label: "Задачи", href: "/workspace/recruiting?view=tasks" },
  { id: "comms", label: "Коммуникации", href: "/workspace/recruiting?view=comms" },
  { id: "activity", label: "Активность", href: "/workspace/recruiting?view=activity" },
  { id: "analytics", label: "Аналитика", href: "/workspace/recruiting?view=analytics" },
  { id: "infra", label: "Инфраструктура", href: "/workspace/recruiting/infra" },
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

export function recruitingConsentLabel(value: unknown): string {
  if (value === true) return "да";
  if (value === false) return "нет";
  return "—";
}

export function recruitingUtmLabel(row: Record<string, unknown>): string {
  const parts = [row.utm_source, row.utm_medium, row.utm_campaign, row.utm_content, row.utm_term]
    .map((x) => (x == null ? "" : String(x).trim()))
    .filter(Boolean);
  return parts.join(" / ") || "—";
}

export function recruitingClickLabel(row: Record<string, unknown>): string {
  const parts: string[] = [];
  if (row.gclid) parts.push(`gclid:${String(row.gclid)}`);
  if (row.fbclid) parts.push(`fbclid:${String(row.fbclid)}`);
  if (row.click_id) parts.push(`click_id:${String(row.click_id)}`);
  return parts.join(" · ") || "—";
}

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
