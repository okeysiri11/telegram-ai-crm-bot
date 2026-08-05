/**
 * Sprint 31.1 — Owner God Mode metrics from platform health + runtime.
 * No second monitoring engine.
 */

import { derivePlatformHealth } from "@/platform-integration/platformHealth";
import { runtimeEngine } from "@/enterprise-runtime/runtimeEngine";
import { jobManager } from "@/enterprise-runtime/jobManager";
import { useNotificationStore } from "@/notifications/notificationStore";
import { listActivity } from "@/workspace-engine/activityJournal";
import { useAuthStore } from "@/auth/authStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";

export type GodModeMetric = {
  id: string;
  title: string;
  value: string;
  route: string;
  tone?: "success" | "warning" | "danger" | "default" | "info";
};

function toneFromHealth(level: string): GodModeMetric["tone"] {
  if (level === "healthy" || level === "ok" || level === "online") return "success";
  if (level === "degraded" || level === "warning" || level === "attention") return "warning";
  if (level === "critical" || level === "err" || level === "error" || level === "offline") return "danger";
  return "default";
}

function toneFromItem(tone: string): GodModeMetric["tone"] {
  if (tone === "ok" || tone === "success" || tone === "healthy") return "success";
  if (tone === "warn" || tone === "warning" || tone === "degraded") return "warning";
  if (tone === "err" || tone === "error" || tone === "critical") return "danger";
  return "default";
}

/** Full Owner God Mode strip — health, runtime, infra, sessions. */
export function deriveGodModeMetrics(): GodModeMetric[] {
  const health = derivePlatformHealth();
  const snap = runtimeEngine.getSnapshot();
  const counts = jobManager.counts();
  const notifs = useNotificationStore.getState().items;
  const unread = notifs.filter((n) => !n.read).length;
  const warnings = notifs.filter(
    (n) => !n.read && (n.kind === "warning" || n.level === "warning"),
  ).length;
  const errors = notifs.filter(
    (n) => !n.read && (n.kind === "error" || n.level === "error" || n.kind === "alert"),
  ).length;
  const activity = listActivity(3);
  const user = useAuthStore.getState().user;
  const roleId = useRoleSwitcher.getState().activeRoleId;
  const sessions = snap.metrics.sessions ?? (user ? 1 : 0);
  const userCount = user ? "1" : "0";
  const orgCount = user?.tenantId?.trim() ? "1" : user ? "1" : "0";

  return [
    {
      id: "platform_health",
      title: "Здоровье платформы",
      value: health.level,
      route: "/health",
      tone: toneFromHealth(health.level),
    },
    {
      id: "ai_runtime",
      title: "AI Runtime",
      value: `${health.runtimeStatus} · ${health.agentsActive} агент.`,
      route: "/platform-builder/runtime",
      tone: toneFromHealth(health.runtimeStatus),
    },
    {
      id: "queues",
      title: "Очереди",
      value: String(health.queueLength),
      route: "/platform-builder/runtime",
      tone: health.queueLength > 20 ? "warning" : "success",
    },
    {
      id: "workers",
      title: "Воркеры",
      value: `${health.workersBusy}/${health.workersTotal}`,
      route: "/platform-builder/runtime",
      tone: health.workersBusy >= health.workersTotal ? "warning" : "success",
    },
    {
      id: "users",
      title: "Пользователи",
      value: userCount,
      route: "/identity/users",
      tone: user ? "success" : "default",
    },
    {
      id: "organizations",
      title: "Организации",
      value: orgCount,
      route: "/identity/organizations",
      tone: orgCount !== "0" ? "success" : "default",
    },
    {
      id: "sessions",
      title: "Активные сессии",
      value: String(sessions),
      route: "/identity/security",
      tone: sessions > 0 ? "success" : "default",
    },
    {
      id: "errors",
      title: "Ошибки",
      value: String(errors || counts.failed || 0),
      route: "/command-runtime",
      tone: errors || counts.failed ? "danger" : "success",
    },
    {
      id: "warnings",
      title: "Предупреждения",
      value: String(warnings || unread),
      route: "/notifications",
      tone: warnings || unread ? "warning" : "success",
    },
    {
      id: "cpu",
      title: "CPU",
      value: `${health.cpuPct}%`,
      route: "/health",
      tone: health.cpuPct > 85 ? "danger" : health.cpuPct > 70 ? "warning" : "success",
    },
    {
      id: "memory",
      title: "Память",
      value: `${health.memoryPct}%`,
      route: "/health",
      tone: health.memoryPct > 85 ? "danger" : health.memoryPct > 70 ? "warning" : "success",
    },
    {
      id: "api",
      title: "API",
      value: health.apiTone,
      route: "/health",
      tone: toneFromItem(health.apiTone),
    },
    {
      id: "database",
      title: "База данных",
      value: health.databaseTone,
      route: "/health",
      tone: toneFromItem(health.databaseTone),
    },
    {
      id: "redis",
      title: "Redis / кэш",
      value: health.cacheTone,
      route: "/health",
      tone: toneFromItem(health.cacheTone),
    },
    {
      id: "security",
      title: "Безопасность",
      value: health.level === "healthy" ? "ok" : health.level,
      route: "/identity/security",
      tone: toneFromHealth(health.level),
    },
    {
      id: "providers",
      title: "Провайдеры",
      value: health.apiTone,
      route: "/ai-studio",
      tone: toneFromItem(health.apiTone),
    },
    {
      id: "jobs",
      title: "Задачи Runtime",
      value: `${counts.running} run · ${counts.waiting} wait`,
      route: "/platform-builder/runtime",
      tone: counts.failed ? "warning" : "info",
    },
    {
      id: "role",
      title: "Режим",
      value: roleId,
      route: "/platform-builder/god-mode",
      tone: "info",
    },
    {
      id: "activity",
      title: "Активность",
      value: activity[0]?.title || "нет",
      route: "/identity/activity",
      tone: "default",
    },
  ];
}
