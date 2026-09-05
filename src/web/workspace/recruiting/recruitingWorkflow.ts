export type WorkflowRow = Record<string, unknown>;

export const LEAD_STATUS_CHOICES = [
  { id: "new", label: "Новый" },
  { id: "qualified", label: "Квалифицирован" },
  { id: "lost", label: "Отклонён" },
] as const;

export const CANDIDATE_FLOW = [
  { id: "NEW", label: "Новый" },
  { id: "QUALIFIED", label: "Квалифицирован" },
  { id: "INTERVIEW", label: "Интервью" },
  { id: "APPROVED", label: "Одобрен" },
  { id: "HIRED", label: "Нанят" },
] as const;

export type RecruiterOption = { id: string; label: string };

function capitalizeWord(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function recruiterLabel(raw: unknown): string {
  const value = String(raw || "").trim();
  if (!value) return "Не назначен";
  const fromEmail = value.includes("@") ? value.split("@")[0] || value : value;
  const parts = fromEmail.split(/[._-]+/).filter(Boolean);
  if (parts[0]?.toLowerCase() === "recruiter" && parts.length > 1) {
    return parts.slice(1).map(capitalizeWord).join(" ");
  }
  return parts.map(capitalizeWord).join(" ") || value;
}

export function isActiveVacancy(row: WorkflowRow): boolean {
  const status = String(row.status || "open").toLowerCase();
  return status !== "closed" && status !== "archived" && status !== "inactive";
}

export function vacancyTitle(row: WorkflowRow | undefined): string {
  if (!row) return "Не выбрана";
  const title = String(row.title || row.name || "").trim();
  return title || "Вакансия";
}

export function vacancyLabelForLead(lead: WorkflowRow, vacancies: WorkflowRow[]): string {
  const id = String(lead.vacancy_id || "").trim();
  if (id) {
    const hit = vacancies.find((v) => String(v.id) === id);
    if (hit) return vacancyTitle(hit);
  }
  const named = String(lead.vacancy || lead.program_of_interest || "").trim();
  return named || "Не выбрана";
}

export function sourceLabel(row: WorkflowRow): string {
  const raw = String(row.source || "").trim().toLowerCase();
  if (!raw) return "—";
  if (raw.includes("vanguard")) return "Vanguard";
  if (raw === "manual") return "Вручную";
  return String(row.source);
}

export function createdLabel(row: WorkflowRow): string {
  const raw = String(row.created_at || row.submitted_at || "").trim();
  if (!raw) return "—";
  return raw.replace("T", " ").replace(/\.\d+Z$/, " UTC").slice(0, 16);
}

export function applicationCount(row: WorkflowRow): number {
  const apps = Array.isArray(row.applications) ? row.applications.length : 0;
  const ids = Array.isArray(row.lead_ids) ? row.lead_ids.filter(Boolean).length : 0;
  const fallback = String(row.lead_id || "").trim() ? 1 : 0;
  return Math.max(apps, ids, fallback);
}

export function applicationCountLabel(row: WorkflowRow): string {
  const n = applicationCount(row);
  if (n === 1) return "1 заявка";
  if (n >= 2 && n <= 4) return `${n} заявки`;
  return `${n} заявок`;
}

export function buildRecruiterOptions(
  rows: WorkflowRow[],
  extra: RecruiterOption[] = [],
  currentUser?: { name?: string; email?: string } | null,
): RecruiterOption[] {
  const out: RecruiterOption[] = [];
  const seen = new Set<string>();
  const add = (id: string, label?: string) => {
    const key = id.trim();
    if (!key || seen.has(key.toLowerCase())) return;
    seen.add(key.toLowerCase());
    out.push({ id: key, label: label || recruiterLabel(key) });
  };
  for (const item of extra) add(item.id, item.label);
  for (const row of rows) {
    const assignee = String(row.assignee || "").trim();
    if (assignee) add(assignee);
  }
  const me = String(currentUser?.name || "").trim() || String(currentUser?.email || "").split("@")[0] || "";
  if (me) add(me);
  return out;
}

export function attentionHref(item: WorkflowRow): string {
  const type = String(item.entity_type || "");
  const id = String(item.entity_id || "");
  if (type === "candidate" && id) return `/workspace/recruiting?view=candidates&id=${encodeURIComponent(id)}`;
  if (type === "task") return "/workspace/recruiting?view=tasks";
  if (id) return `/workspace/recruiting?view=leads&id=${encodeURIComponent(id)}`;
  return "/workspace/recruiting?view=leads";
}

export function canSelectLeadStatus(status: string): boolean {
  return status !== "converted";
}

export function recruitingCanMerge(role: string): boolean {
  return role === "recruiter" || role === "owner" || role === "platform_owner";
}

export function recruitingCanForceMerge(role: string): boolean {
  return role === "owner" || role === "platform_owner";
}

export function candidateSourceList(row: WorkflowRow): string {
  const apps = Array.isArray(row.applications) ? (row.applications as WorkflowRow[]) : [];
  const values = [sourceLabel(row), ...apps.map((app) => sourceLabel(app))].filter((value) => value && value !== "—");
  return [...new Set(values)].join(", ") || "—";
}

const TEST_TRAFFIC_MARKERS = ["e2e_test", "e2e-historical", "vanguard_e2e", "e2e-"];

export function isTestTraffic(row: WorkflowRow | null | undefined): boolean {
  if (!row) return false;
  const cls = String(row.traffic_class || "").toUpperCase();
  if (cls === "TEST" || cls === "E2E") return true;
  if (String(row.data_mode || "").toUpperCase() === "TEST") return true;
  const blob = [
    row.utm_source,
    row.utm_medium,
    row.utm_campaign,
    row.source,
    row.first_touch_source,
    row.first_touch_campaign,
    row.external_id,
  ]
    .map((value) => String(value || "").toLowerCase())
    .join(" ");
  if (TEST_TRAFFIC_MARKERS.some((marker) => blob.includes(marker))) return true;
  const apps = Array.isArray(row.applications) ? (row.applications as WorkflowRow[]) : [];
  return apps.some((app) => isTestTraffic(app));
}

export function trafficLabel(row: WorkflowRow): string {
  return isTestTraffic(row) ? "TEST" : "";
}

export function candidateVacancyList(row: WorkflowRow, vacancies: WorkflowRow[]): string {
  const apps = Array.isArray(row.applications) ? (row.applications as WorkflowRow[]) : [];
  const values = [
    vacancyLabelForLead(row, vacancies),
    ...apps.map((app) => vacancyLabelForLead(app, vacancies)),
  ].filter((value) => value && value !== "Не выбрана");
  return [...new Set(values)].join(", ") || "Не выбрана";
}
