/**
 * Enterprise Intelligence derivation — Sprint 32.5.
 * Pure client layer over LiveEnterpriseSnapshot + notifications.
 * No new Engine / AI Core / Concierge.
 */

import type { LiveEnterpriseSnapshot } from "@/live-ops";
import type { AppNotification } from "@/notifications/notificationStore";

export type InsightCategory = "event" | "anomaly" | "risk" | "achievement" | "opportunity";

export type EnterpriseInsight = {
  id: string;
  category: InsightCategory;
  title: string;
  detail: string;
  route?: string;
};

export type DailyBrief = {
  greeting: string;
  bullets: string[];
  generatedAt: string;
};

export type PriorityBucket = "urgent" | "important" | "awaiting" | "recommended";

export type SmartPriority = {
  id: string;
  bucket: PriorityBucket;
  title: string;
  detail: string;
  route?: string;
  score: number;
};

export type CrossModuleLink = {
  id: string;
  from: string;
  to: string;
  title: string;
  detail: string;
  route?: string;
};

export type ExecutiveDecision = {
  decideToday: SmartPriority[];
  canWait: SmartPriority[];
  risks: EnterpriseInsight[];
  opportunities: EnterpriseInsight[];
};

export type IntelligenceBundle = {
  insights: EnterpriseInsight[];
  brief: DailyBrief;
  priorities: SmartPriority[];
  crossModule: CrossModuleLink[];
  decision: ExecutiveDecision;
  knowledgeAware: boolean;
};

const CROSS_RULES: Array<{ from: string; to: string; title: string; detail: string; route: string }> = [
  {
    from: "crm",
    to: "finance",
    title: "CRM → Finance",
    detail: "Сделки и клиенты влияют на выручку и казначейство",
    route: "/workspace/finance",
  },
  {
    from: "documents",
    to: "legal",
    title: "Documents → Legal",
    detail: "Новые документы требуют юридической проверки",
    route: "/workspace/legal",
  },
  {
    from: "knowledge",
    to: "legal",
    title: "Knowledge → Legal",
    detail: "База знаний обновлена — проверить compliance",
    route: "/platform-builder/knowledge",
  },
  {
    from: "marketing",
    to: "sales",
    title: "Marketing → Sales",
    detail: "Кампании влияют на воронку продаж",
    route: "/workspace/crm",
  },
  {
    from: "ai",
    to: "crm",
    title: "AI → CRM",
    detail: "AI-автоматизации меняют приоритеты по клиентам",
    route: "/workspace/crm",
  },
  {
    from: "automation",
    to: "production",
    title: "Automation → Production",
    detail: "Завершённые автоматизации влияют на операционный контур",
    route: "/enterprise-city",
  },
];

function greetingForHour(hour: number): string {
  if (hour < 12) return "Доброе утро.";
  if (hour < 18) return "Добрый день.";
  return "Добрый вечер.";
}

function moduleTokens(snapshot: LiveEnterpriseSnapshot): Set<string> {
  const set = new Set(snapshot.activeModules.map((m) => m.toLowerCase()));
  for (const a of snapshot.activity) {
    if (a.moduleHint) set.add(a.moduleHint.toLowerCase());
    const blob = `${a.title} ${a.detail}`.toLowerCase();
    if (blob.includes("crm") || blob.includes("клиент") || blob.includes("сделк")) set.add("crm");
    if (blob.includes("financ") || blob.includes("финанс") || blob.includes("invoice")) set.add("finance");
    if (blob.includes("legal") || blob.includes("договор")) set.add("legal");
    if (blob.includes("market")) set.add("marketing");
    if (blob.includes("sales") || blob.includes("продаж")) set.add("sales");
    if (blob.includes("knowledge") || blob.includes("документ") || blob.includes("docs")) {
      set.add("knowledge");
      set.add("documents");
    }
    if (blob.includes("ai") || a.kind === "ai") set.add("ai");
    if (a.kind === "automation") set.add("automation");
  }
  return set;
}

function knowledgeSignal(snapshot: LiveEnterpriseSnapshot): boolean {
  const kbHealth = snapshot.health.find((h) => h.id === "knowledge" || h.id === "documents");
  const tokens = moduleTokens(snapshot);
  const fromRec = snapshot.recommendations.some((r) =>
    /knowledge|document|docs|баз[аы] знан/i.test(r.title),
  );
  const fromActivity = tokens.has("knowledge") || tokens.has("documents");
  return Boolean((kbHealth?.ok && (fromActivity || fromRec)) || fromActivity || fromRec);
}

export function deriveInsights(
  snapshot: LiveEnterpriseSnapshot,
  unread: AppNotification[],
): EnterpriseInsight[] {
  const out: EnterpriseInsight[] = [];
  const today = snapshot.timeline.find((b) => b.id === "today");
  for (const item of (today?.items || []).slice(0, 3)) {
    out.push({
      id: `ev_${out.length}`,
      category: "event",
      title: item,
      detail: "Главные события дня",
      route: "/dashboard",
    });
  }
  for (const a of snapshot.activity.slice(0, 2)) {
    if (out.some((i) => i.title === a.title)) continue;
    out.push({
      id: `ev_act_${a.id}`,
      category: "event",
      title: a.title,
      detail: a.detail || a.source,
      route: "/dashboard",
    });
  }

  for (const h of snapshot.health.filter((x) => !x.ok).slice(0, 3)) {
    out.push({
      id: `an_${h.id}`,
      category: "anomaly",
      title: `Отклонение: ${h.label}`,
      detail: h.detail || "Сервис вне нормы",
      route: "/platform-builder/mission-control",
    });
  }

  for (const r of snapshot.recommendations.filter((x) => x.tone === "risk").slice(0, 3)) {
    out.push({
      id: `risk_${r.id}`,
      category: "risk",
      title: r.title,
      detail: "Риск из Intelligence",
      route: "/dashboard?mode=executive",
    });
  }
  for (const e of snapshot.aiOps.errors.slice(0, 2)) {
    out.push({
      id: `risk_err_${out.length}`,
      category: "risk",
      title: e,
      detail: "AI Ops error",
      route: "/platform-builder/ai-team",
    });
  }

  for (const done of snapshot.aiOps.completed.slice(0, 2)) {
    out.push({
      id: `ach_${out.length}`,
      category: "achievement",
      title: `AI завершил: ${done}`,
      detail: "Автоматизация выполнена",
      route: "/platform-builder/ai-team",
    });
  }
  if (snapshot.mcOk) {
    out.push({
      id: "ach_mc",
      category: "achievement",
      title: "Mission Control в норме",
      detail: "Операционный контур стабилен",
      route: "/platform-builder/mission-control",
    });
  }

  for (const r of snapshot.recommendations.filter((x) => x.tone === "improve" || x.tone === "suggest").slice(0, 3)) {
    out.push({
      id: `opp_${r.id}`,
      category: "opportunity",
      title: r.title,
      detail: "Потенциальная возможность",
      route: "/dashboard",
    });
  }
  if (knowledgeSignal(snapshot)) {
    out.push({
      id: "opp_kb",
      category: "opportunity",
      title: "Новые документы в Knowledge Base",
      detail: "AI учитывает обновления базы знаний",
      route: "/platform-builder/knowledge",
    });
  }
  for (const n of unread.filter((x) => x.kind === "ai").slice(0, 1)) {
    out.push({
      id: `opp_notif_${n.id}`,
      category: "opportunity",
      title: n.title,
      detail: n.body || "AI insight",
      route: "/dashboard",
    });
  }

  const order: InsightCategory[] = ["risk", "anomaly", "event", "achievement", "opportunity"];
  return out
    .sort((a, b) => order.indexOf(a.category) - order.indexOf(b.category))
    .slice(0, 12);
}

export function deriveDailyBrief(
  snapshot: LiveEnterpriseSnapshot,
  unread: AppNotification[],
  now = new Date(),
): DailyBrief {
  const tasks = snapshot.activity.filter((a) => a.kind === "task").length || snapshot.aiOps.queue.length;
  const overdueish = snapshot.recommendations.filter((r) => r.tone === "risk").length;
  const automations = snapshot.aiOps.completed.length || snapshot.aiOps.recent.length;
  const clientsAttention = unread.filter((n) => /client|клиент|crm|deal|сделк/i.test(`${n.title} ${n.body}`)).length
    || snapshot.activity.filter((a) => /клиент|сделк|crm/i.test(a.title)).length;
  const events = snapshot.timeline.find((b) => b.id === "today")?.items.length || snapshot.activity.length;

  const bullets = [
    `${Math.max(tasks, events)} новых сигналов / задач`,
    `${overdueish} просроченных / рисковых сделок (по AI)`,
    `AI завершил ${Math.max(automations, 1)} автоматизаций`,
    `внимание требуется ${Math.max(clientsAttention, unread.length ? 1 : 0)} клиентам / сигналам`,
  ];
  if (knowledgeSignal(snapshot)) {
    bullets.push("в Knowledge Base есть обновления документов");
  }
  const failed = snapshot.health.filter((h) => !h.ok).length;
  if (failed) bullets.push(`${failed} сервиса требуют проверки health`);

  return {
    greeting: greetingForHour(now.getHours()),
    bullets: bullets.slice(0, 6),
    generatedAt: now.toISOString(),
  };
}

export function derivePriorities(
  snapshot: LiveEnterpriseSnapshot,
  unread: AppNotification[],
): SmartPriority[] {
  const list: SmartPriority[] = [];

  for (const h of snapshot.health.filter((x) => !x.ok)) {
    list.push({
      id: `u_health_${h.id}`,
      bucket: "urgent",
      title: `Восстановить ${h.label}`,
      detail: h.detail || "Health anomaly",
      route: "/platform-builder/mission-control",
      score: 100,
    });
  }
  for (const r of snapshot.recommendations.filter((x) => x.tone === "risk")) {
    list.push({
      id: `u_risk_${r.id}`,
      bucket: "urgent",
      title: r.title,
      detail: "Срочный риск",
      route: "/dashboard?mode=executive",
      score: 95,
    });
  }
  for (const e of snapshot.aiOps.errors.slice(0, 2)) {
    list.push({
      id: `u_err_${list.length}`,
      bucket: "urgent",
      title: e,
      detail: "AI Ops",
      route: "/platform-builder/ai-team",
      score: 90,
    });
  }

  for (const r of snapshot.recommendations.filter((x) => x.tone === "today")) {
    list.push({
      id: `i_today_${r.id}`,
      bucket: "important",
      title: r.title,
      detail: "Важно сегодня",
      route: "/dashboard",
      score: 70,
    });
  }
  for (const a of snapshot.activity.filter((x) => x.kind === "task" || x.kind === "notification").slice(0, 3)) {
    list.push({
      id: `i_act_${a.id}`,
      bucket: "important",
      title: a.title,
      detail: a.detail || "Активность",
      route: "/dashboard",
      score: 65,
    });
  }

  for (const n of unread.slice(0, 4)) {
    list.push({
      id: `a_notif_${n.id}`,
      bucket: "awaiting",
      title: n.title,
      detail: n.body || "Ожидает решения",
      route: "/dashboard",
      score: 55,
    });
  }
  for (const q of snapshot.aiOps.queue.slice(0, 3)) {
    list.push({
      id: `a_q_${list.length}`,
      bucket: "awaiting",
      title: q,
      detail: "В очереди AI",
      route: "/platform-builder/ai-team",
      score: 50,
    });
  }

  for (const r of snapshot.recommendations.filter((x) => x.tone === "suggest" || x.tone === "improve")) {
    list.push({
      id: `r_rec_${r.id}`,
      bucket: "recommended",
      title: r.title,
      detail: "Рекомендуемое действие",
      route: "/dashboard",
      score: 40,
    });
  }
  if (knowledgeSignal(snapshot)) {
    list.push({
      id: "r_kb",
      bucket: "recommended",
      title: "Просмотреть новые документы",
      detail: "Knowledge awareness",
      route: "/platform-builder/knowledge",
      score: 42,
    });
  }

  return list.sort((a, b) => b.score - a.score).slice(0, 16);
}

export function deriveCrossModule(snapshot: LiveEnterpriseSnapshot): CrossModuleLink[] {
  const tokens = moduleTokens(snapshot);
  const links: CrossModuleLink[] = [];
  for (const rule of CROSS_RULES) {
    if (tokens.has(rule.from) || tokens.has(rule.to) || snapshot.activeModules.length === 0) {
      // Always surface core CRM→Finance & Marketing→Sales lightly when platform active
      const force =
        (rule.from === "crm" && rule.to === "finance") ||
        (rule.from === "marketing" && rule.to === "sales");
      if (!tokens.has(rule.from) && !force && !knowledgeSignal(snapshot)) continue;
      if (rule.from === "knowledge" || rule.from === "documents") {
        if (!knowledgeSignal(snapshot) && !tokens.has("documents") && !tokens.has("knowledge")) continue;
      }
      links.push({
        id: `x_${rule.from}_${rule.to}`,
        from: rule.from,
        to: rule.to,
        title: rule.title,
        detail: rule.detail,
        route: rule.route,
      });
    }
  }
  if (!links.length) {
    links.push({
      id: "x_default_crm_fin",
      from: "crm",
      to: "finance",
      title: "CRM → Finance",
      detail: "Связь модулей доступна для анализа",
      route: "/workspace/finance",
    });
  }
  return links.slice(0, 5);
}

export function deriveDecision(
  priorities: SmartPriority[],
  insights: EnterpriseInsight[],
): ExecutiveDecision {
  return {
    decideToday: priorities.filter((p) => p.bucket === "urgent" || p.bucket === "important").slice(0, 4),
    canWait: priorities.filter((p) => p.bucket === "awaiting" || p.bucket === "recommended").slice(0, 4),
    risks: insights.filter((i) => i.category === "risk" || i.category === "anomaly").slice(0, 4),
    opportunities: insights.filter((i) => i.category === "opportunity" || i.category === "achievement").slice(0, 4),
  };
}

export function deriveIntelligence(
  snapshot: LiveEnterpriseSnapshot,
  notifications: AppNotification[],
  now = new Date(),
): IntelligenceBundle {
  const unread = notifications.filter((n) => !n.read);
  const insights = deriveInsights(snapshot, unread);
  const brief = deriveDailyBrief(snapshot, unread, now);
  const priorities = derivePriorities(snapshot, unread);
  const crossModule = deriveCrossModule(snapshot);
  const decision = deriveDecision(priorities, insights);
  return {
    insights,
    brief,
    priorities,
    crossModule,
    decision,
    knowledgeAware: knowledgeSignal(snapshot),
  };
}
