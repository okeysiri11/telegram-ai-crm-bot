/**
 * Live Enterprise snapshot fetcher — Sprint 32.3.4.
 * Aggregates existing MC / Ops / Intelligence / notifications.
 * No new AI Engine, Event Bus, or Notification System.
 */

import { apiFetch } from "@/integrations/apiClient";
import { PLATFORM_BUILDER_API } from "../../platform-builder/types";
import { recentActivity } from "../../workspace/managers/recentActivity";
import type { AppNotification } from "@/notifications/notificationStore";
import {
  ENTERPRISE_HEALTH_PROBES,
  SEED_ACTIVITY,
  type HealthServiceId,
  type LiveActivityItem,
} from "./liveEnterpriseCatalog";

export type AiOpsSnapshot = {
  running: string[];
  queue: string[];
  recent: string[];
  status: string;
  errors: string[];
  completed: string[];
};

export type TimelineBucket = {
  id: "today" | "last_hour" | "recent" | "next";
  label: string;
  items: string[];
};

export type HealthStatus = {
  id: HealthServiceId;
  label: string;
  ok: boolean;
  detail: string;
};

export type RecommendationItem = {
  id: string;
  title: string;
  tone: "suggest" | "today" | "risk" | "improve";
};

export type LiveEnterpriseSnapshot = {
  updatedAt: string;
  activity: LiveActivityItem[];
  aiOps: AiOpsSnapshot;
  timeline: TimelineBucket[];
  health: HealthStatus[];
  recommendations: RecommendationItem[];
  mcOk: boolean;
  activeModules: string[];
};

type Dict = Record<string, unknown>;

function asList(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

function str(v: unknown, fallback = ""): string {
  return typeof v === "string" && v.trim() ? v : fallback;
}

function flattenStrings(v: unknown, limit = 8): string[] {
  const out: string[] = [];
  for (const item of asList(v)) {
    if (typeof item === "string") out.push(item);
    else if (item && typeof item === "object") {
      const o = item as Dict;
      const label = str(o.title) || str(o.name) || str(o.label) || str(o.summary) || str(o.message);
      if (label) out.push(label);
    }
    if (out.length >= limit) break;
  }
  return out;
}

async function safeJson(url: string): Promise<Dict | null> {
  try {
    const res = await apiFetch(url);
    if (!res.ok) return null;
    return (await res.json()) as Dict;
  } catch {
    return null;
  }
}

function notifToActivity(n: AppNotification): LiveActivityItem {
  const kindMap: Record<string, LiveActivityItem["kind"]> = {
    ai: "ai",
    workflow: "automation",
    task: "task",
    alert: "notification",
    toast: "notification",
    in_app: "notification",
  };
  return {
    id: `notif_${n.id}`,
    kind: kindMap[n.kind] || "notification",
    title: n.title || "Получено уведомление",
    detail: n.body || "",
    at: n.createdAt,
    source: "notifications",
    moduleHint: n.kind === "ai" ? "ai" : "hub",
  };
}

function normalizeMcActivity(raw: Dict | null): LiveActivityItem[] {
  if (!raw) return [];
  const streams = asList(raw.streams ?? raw.activity ?? raw.items ?? raw.events);
  return streams.slice(0, 12).map((item, i) => {
    if (typeof item === "string") {
      return {
        id: `mc_${i}`,
        kind: "system" as const,
        title: item,
        detail: "Mission Control",
        at: new Date(Date.now() - i * 60_000).toISOString(),
        source: "mission_control" as const,
      };
    }
    const o = (item || {}) as Dict;
    return {
      id: str(o.id, `mc_${i}`),
      kind: (str(o.kind, "system") as LiveActivityItem["kind"]) || "system",
      title: str(o.title) || str(o.summary) || str(o.message) || "MC event",
      detail: str(o.detail) || str(o.source) || "mission-control",
      at: str(o.at) || str(o.timestamp) || new Date(Date.now() - i * 60_000).toISOString(),
      source: "mission_control" as const,
      moduleHint: str(o.module) || undefined,
    };
  });
}

function normalizeOpsActivity(raw: Dict | null): LiveActivityItem[] {
  if (!raw) return [];
  const events = asList(raw.events ?? raw.activity ?? raw.items ?? raw.realtime);
  return events.slice(0, 10).map((item, i) => {
    if (typeof item === "string") {
      return {
        id: `ops_${i}`,
        kind: "system" as const,
        title: item,
        detail: "Operations",
        at: new Date(Date.now() - i * 90_000).toISOString(),
        source: "operations" as const,
      };
    }
    const o = (item || {}) as Dict;
    return {
      id: str(o.id, `ops_${i}`),
      kind: "system" as const,
      title: str(o.title) || str(o.summary) || str(o.message) || "Ops event",
      detail: str(o.detail) || "operations",
      at: str(o.at) || new Date(Date.now() - i * 90_000).toISOString(),
      source: "operations" as const,
    };
  });
}

function buildAiOps(mc: Dict | null, panels: Dict | null, intel: Dict | null): AiOpsSnapshot {
  const running =
    flattenStrings(panels?.running ?? panels?.agents ?? mc?.active_ai) ||
    ["Sales Specialist", "Ops Concierge", "Risk Monitor"];
  const queue = flattenStrings(panels?.queue ?? panels?.tasks) || ["Review CRM brief", "Classify feedback"];
  const recent =
    flattenStrings(panels?.recent ?? intel?.recent) ||
    ["Подготовлен brief по сделкам", "Напомнено о дедлайне договора"];
  const errors = flattenStrings(panels?.errors ?? mc?.errors);
  const completed =
    flattenStrings(panels?.completed ?? panels?.automations) || ["Follow-up · 12", "Feedback · 8"];
  const status = str(mc?.status) || str(panels?.status) || (mc ? "operational" : "degraded");
  return { running: running.slice(0, 6), queue: queue.slice(0, 6), recent: recent.slice(0, 6), status, errors: errors.slice(0, 4), completed: completed.slice(0, 6) };
}

function buildTimeline(activity: LiveActivityItem[], timelineRaw: Dict | null): TimelineBucket[] {
  const now = Date.now();
  const hourAgo = now - 60 * 60_000;
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const todayTs = todayStart.getTime();

  const titles = activity.map((a) => a.title);
  const lastHour = activity.filter((a) => Date.parse(a.at) >= hourAgo).map((a) => a.title);
  const today = activity.filter((a) => Date.parse(a.at) >= todayTs).map((a) => a.title);

  const segments = asList(timelineRaw?.segments ?? timelineRaw?.items ?? timelineRaw?.timeline);
  const nextFromApi = flattenStrings(segments).slice(0, 4);
  const next =
    nextFromApi.length > 0
      ? nextFromApi
      : ["Подтвердить AI recommendation", "Проверить воронку CRM", "Открыть Mission Control"];

  return [
    { id: "today", label: "Сегодня", items: (today.length ? today : titles).slice(0, 5) },
    { id: "last_hour", label: "Последний час", items: (lastHour.length ? lastHour : titles.slice(0, 3)).slice(0, 5) },
    { id: "recent", label: "Последние действия", items: titles.slice(0, 5) },
    { id: "next", label: "Следующие задачи", items: next.slice(0, 5) },
  ];
}

function buildRecommendations(intel: Dict | null, panels: Dict | null): RecommendationItem[] {
  const raw = [
    ...flattenStrings(intel?.recommendations ?? intel?.items),
    ...flattenStrings(panels?.recommendations),
  ];
  if (raw.length) {
    return raw.slice(0, 6).map((title, i) => ({
      id: `rec_${i}`,
      title,
      tone: (i % 4 === 0 ? "risk" : i % 3 === 0 ? "improve" : i % 2 === 0 ? "today" : "suggest") as RecommendationItem["tone"],
    }));
  }
  return [
    { id: "r1", title: "AI рекомендует открыть Mission Control для проверки экосистем", tone: "suggest" },
    { id: "r2", title: "Сегодня желательно согласовать договор #884", tone: "today" },
    { id: "r3", title: "Обнаружены риски: backlog Critical feedback в Pilot", tone: "risk" },
    { id: "r4", title: "Найдено улучшение: автоматизировать follow-up в CRM", tone: "improve" },
  ];
}

function activeModulesFromActivity(activity: LiveActivityItem[]): string[] {
  const hints = new Set<string>();
  for (const a of activity.slice(0, 12)) {
    if (a.moduleHint) hints.add(a.moduleHint);
    if (a.kind === "crm" || a.kind === "client" || a.kind === "deal") hints.add("crm");
    if (a.kind === "ai" || a.kind === "automation") hints.add("ai");
    if (a.kind === "document") hints.add("documents");
  }
  return [...hints];
}

export async function fetchLiveEnterpriseSnapshot(
  notifications: AppNotification[],
): Promise<LiveEnterpriseSnapshot> {
  const [mcStatus, mcActivity, opsActivity, mcTimeline, mcPanels, intelRecs] = await Promise.all([
    safeJson(`${PLATFORM_BUILDER_API}/mission-control/status`),
    safeJson(`${PLATFORM_BUILDER_API}/mission-control/activity`),
    safeJson(`${PLATFORM_BUILDER_API}/operations/activity`),
    safeJson(`${PLATFORM_BUILDER_API}/mission-control/timeline`),
    safeJson(`${PLATFORM_BUILDER_API}/mission-control/panels`),
    safeJson(`${PLATFORM_BUILDER_API}/intelligence/recommendations`),
  ]);

  const healthResults = await Promise.all(
    ENTERPRISE_HEALTH_PROBES.map(async (p) => {
      const body = await safeJson(p.healthUrl);
      const ok = Boolean(body);
      return {
        id: p.id,
        label: p.label,
        ok,
        detail: ok ? str(body?.status, "ok") : "check",
      } satisfies HealthStatus;
    }),
  );

  const fromNotifs = notifications.slice(0, 8).map(notifToActivity);
  const fromRecent = recentActivity.list().slice(0, 6).map((r, i) => ({
    id: `ra_${r.id}`,
    kind: (r.kind === "ai" ? "ai" : r.kind === "document" ? "document" : r.kind === "task" ? "task" : "system") as LiveActivityItem["kind"],
    title: r.summary,
    detail: r.kind,
    at: r.at,
    source: "recent" as const,
  }));

  const merged = [
    ...normalizeMcActivity(mcActivity),
    ...normalizeOpsActivity(opsActivity),
    ...fromNotifs,
    ...fromRecent,
    ...SEED_ACTIVITY,
  ]
    .sort((a, b) => Date.parse(b.at) - Date.parse(a.at))
    .filter((item, idx, arr) => arr.findIndex((x) => x.title === item.title && x.source === item.source) === idx)
    .slice(0, 24);

  const aiOps = buildAiOps(mcStatus, mcPanels, intelRecs);
  const timeline = buildTimeline(merged, mcTimeline);
  const recommendations = buildRecommendations(intelRecs, mcPanels);

  return {
    updatedAt: new Date().toISOString(),
    activity: merged,
    aiOps,
    timeline,
    health: healthResults,
    recommendations,
    mcOk: Boolean(mcStatus),
    activeModules: activeModulesFromActivity(merged),
  };
}

export function emptyLiveSnapshot(): LiveEnterpriseSnapshot {
  return {
    updatedAt: new Date(0).toISOString(),
    activity: SEED_ACTIVITY,
    aiOps: {
      running: ["Sales Specialist", "Ops Concierge"],
      queue: ["Review CRM brief"],
      recent: ["Seed activity"],
      status: "seed",
      errors: [],
      completed: ["Follow-up · 12"],
    },
    timeline: buildTimeline(SEED_ACTIVITY, null),
    health: ENTERPRISE_HEALTH_PROBES.map((p) => ({
      id: p.id,
      label: p.label,
      ok: true,
      detail: "seed",
    })),
    recommendations: buildRecommendations(null, null),
    mcOk: false,
    activeModules: ["crm", "ai"],
  };
}
