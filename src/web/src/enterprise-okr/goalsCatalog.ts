/**
 * Enterprise Goals catalog — Sprint 33.8.
 * Static goal definitions only — no new Store / Strategy Engine.
 */

export type GoalDomain =
  | "revenue"
  | "profit"
  | "sales"
  | "marketing"
  | "production"
  | "customer_success"
  | "hr"
  | "operations";

export type GoalPriority = "p0" | "p1" | "p2";

export type EnterpriseGoalDef = {
  id: string;
  domain: GoalDomain;
  label: string;
  objective: string;
  kpi: string;
  owner: string;
  priority: GoalPriority;
  deadline: string;
  /** Baseline progress seed 0–100 before live signals. */
  baseProgress: number;
  keyResults: string[];
  tokens: RegExp;
};

export const ENTERPRISE_GOALS: EnterpriseGoalDef[] = [
  {
    id: "g_revenue",
    domain: "revenue",
    label: "Revenue",
    objective: "Увеличить выручку организации",
    kpi: "MRR / pipeline value",
    owner: "CEO / Finance",
    priority: "p0",
    deadline: "2026-12-31",
    baseProgress: 48,
    keyResults: ["+20% MRR", "Pipeline coverage ×3", "Win rate ≥ 28%"],
    tokens: /revenue|выручк|mrr|finance|deal|сделк/i,
  },
  {
    id: "g_profit",
    domain: "profit",
    label: "Profit",
    objective: "Повысить маржинальность и контроль затрат",
    kpi: "Gross margin %",
    owner: "CFO",
    priority: "p0",
    deadline: "2026-12-31",
    baseProgress: 42,
    keyResults: ["Margin +4pp", "Cost per deal −12%", "Refund rate < 3%"],
    tokens: /profit|margin|марж|cost|затрат|refund/i,
  },
  {
    id: "g_sales",
    domain: "sales",
    label: "Sales",
    objective: "Ускорить цикл продаж и конверсию",
    kpi: "Deals closed / cycle days",
    owner: "Head of Sales",
    priority: "p0",
    deadline: "2026-09-30",
    baseProgress: 55,
    keyResults: ["Cycle −15%", "SQL→Won +8pp", "AI follow-up coverage 90%"],
    tokens: /sales|crm|lead|client|продаж|сделк/i,
  },
  {
    id: "g_marketing",
    domain: "marketing",
    label: "Marketing",
    objective: "Масштабировать квалифицированный спрос",
    kpi: "MQL / CAC",
    owner: "CMO",
    priority: "p1",
    deadline: "2026-10-31",
    baseProgress: 50,
    keyResults: ["MQL +25%", "CAC −10%", "Campaign→CRM sync 100%"],
    tokens: /marketing|campaign|mql|лид|маркетинг/i,
  },
  {
    id: "g_production",
    domain: "production",
    label: "Production",
    objective: "Сократить cycle time операционных процессов",
    kpi: "Avg process time",
    owner: "COO",
    priority: "p1",
    deadline: "2026-11-15",
    baseProgress: 46,
    keyResults: ["Cycle −20%", "Queue < 3", "Automation coverage +30%"],
    tokens: /production|runtime|queue|workflow|процесс|производ/i,
  },
  {
    id: "g_cs",
    domain: "customer_success",
    label: "Customer Success",
    objective: "Удержать клиентов и снизить churn",
    kpi: "NPS / churn %",
    owner: "Head of CS",
    priority: "p1",
    deadline: "2026-12-01",
    baseProgress: 58,
    keyResults: ["Churn < 4%", "NPS ≥ 45", "SLA breaches −50%"],
    tokens: /customer|churn|nps|support|клиент|retention/i,
  },
  {
    id: "g_hr",
    domain: "hr",
    label: "HR",
    objective: "Усилить AI Team и операционную ёмкость",
    kpi: "AI success % / hire ramp",
    owner: "People / AI Team Lead",
    priority: "p2",
    deadline: "2026-08-31",
    baseProgress: 40,
    keyResults: ["AI success ≥ 80%", "Skill coverage +3 packs", "Onboarding < 7 дней"],
    tokens: /hr|hire|team|ai team|onboard|сотрудник/i,
  },
  {
    id: "g_ops",
    domain: "operations",
    label: "Operations",
    objective: "Стабилизировать Runtime и интеграции",
    kpi: "Uptime / failed tasks",
    owner: "Ops Lead",
    priority: "p0",
    deadline: "2026-09-15",
    baseProgress: 52,
    keyResults: ["Failed tasks < 2%", "Integrations setup gaps = 0", "Autonomy L2–L3 on low-risk"],
    tokens: /ops|operation|integration|runtime|error|сбо[йи]/i,
  },
];

export function getGoalDef(id: string): EnterpriseGoalDef | undefined {
  return ENTERPRISE_GOALS.find((g) => g.id === id);
}
