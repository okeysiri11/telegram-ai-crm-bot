/**
 * Sprint 30.8 / 32.5 — Live Owner dashboard metrics from existing stores/runtime.
 * Closed Beta: no stub labels ("identity" / "live") — session-derived counts.
 */

import { readCrmCache } from "./crmApi";
import { countProjects } from "./ProjectsModulePage";
import { countKnowledge } from "./KnowledgeModulePage";
import { countCalendarEvents } from "./CalendarModulePage";
import { countDriveFiles } from "./DriveModulePage";
import { DEFAULT_AGENTS } from "@/enterprise-runtime/defaultAgents";
import { derivePlatformHealth } from "@/platform-integration/platformHealth";
import { useNotificationStore } from "@/notifications/notificationStore";
import { listActivity } from "@/workspace-engine/activityJournal";
import { listInstalled } from "@/enterprise-marketplace/installState";
import { aiAgentRuntime } from "@/enterprise-runtime/aiAgentRuntime";
import { jobManager } from "@/enterprise-runtime/jobManager";
import { useAuthStore } from "@/auth/authStore";
import { securityCenter } from "../../auth/managers/securityCenter";

export type OwnerMetricCard = {
  id: string;
  title: string;
  value: string;
  route: string;
  tone?: "success" | "warning" | "default";
};

function sessionIdentityCounts(): { users: string; orgs: string } {
  const { user } = useAuthStore.getState();
  const users = user ? "1" : "0";
  const orgs = user?.tenantId?.trim() ? "1" : user ? "1" : "0";
  return { users, orgs };
}

export function deriveOwnerMetrics(): OwnerMetricCard[] {
  const crm = readCrmCache();
  const health = derivePlatformHealth();
  const unread = useNotificationStore.getState().items.filter((n) => !n.read).length;
  const activity = listActivity(1);
  const agentsLive = aiAgentRuntime.activeCount();
  const counts = jobManager.counts();
  const { users, orgs } = sessionIdentityCounts();
  const sec = securityCenter.snapshot();
  const providerTone =
    health.apiTone === "ok" || health.apiTone === "healthy" ? "success" : "warning";

  return [
    {
      id: "users",
      title: "Пользователи",
      value: users,
      route: "/identity/users",
      tone: users !== "0" ? "success" : "default",
    },
    {
      id: "orgs",
      title: "Организации",
      value: orgs,
      route: "/identity/organizations",
      tone: orgs !== "0" ? "success" : "default",
    },
    {
      id: "ai",
      title: "AI-агенты",
      value: `${agentsLive}/${DEFAULT_AGENTS.length}`,
      route: "/ai-agents",
      tone: agentsLive > 0 ? "success" : "default",
    },
    {
      id: "crm",
      title: "CRM",
      value: `${crm.clients.length} кл. · ${crm.deals.length} сд.`,
      route: "/crm",
      tone: "success",
    },
    {
      id: "projects",
      title: "Проекты",
      value: String(countProjects()),
      route: "/projects",
      tone: "success",
    },
    {
      id: "runtime",
      title: "Runtime",
      value: health.runtimeStatus,
      route: "/platform-builder/runtime",
      tone: health.runtimeStatus === "healthy" ? "success" : "warning",
    },
    {
      id: "security",
      title: "Безопасность",
      value: `${sec.health ?? "ok"} · риск ${sec.riskScore}`,
      route: "/identity/security",
      tone: sec.health === "critical" ? "warning" : "success",
    },
    {
      id: "queues",
      title: "Очереди",
      value: `${counts.waiting + counts.running} акт.`,
      route: "/platform-builder/runtime",
      tone: counts.failed ? "warning" : "success",
    },
    {
      id: "health",
      title: "Здоровье",
      value: `${health.level} · CPU ${health.cpuPct}%`,
      route: "/health",
      tone: health.level === "healthy" ? "success" : "warning",
    },
    {
      id: "api",
      title: "API",
      value: health.apiTone,
      route: "/health",
      tone: providerTone,
    },
    {
      id: "database",
      title: "База данных",
      value: health.databaseTone,
      route: "/health",
      tone: health.databaseTone === "ok" || health.databaseTone === "healthy" ? "success" : "warning",
    },
    {
      id: "redis",
      title: "Redis",
      value: health.cacheTone,
      route: "/health",
      tone: health.cacheTone === "ok" || health.cacheTone === "healthy" ? "success" : "warning",
    },
    {
      id: "providers",
      title: "Провайдеры",
      value: health.apiTone,
      route: "/ai-studio",
      tone: providerTone,
    },
    {
      id: "ai_usage",
      title: "AI Usage",
      value: `${agentsLive} агент. · ${counts.running} job`,
      route: "/ai-agents",
      tone: "default",
    },
    {
      id: "notifications",
      title: "Уведомления",
      value: `${unread} непроч.`,
      route: "/notifications",
      tone: unread ? "warning" : "success",
    },
    {
      id: "activity",
      title: "Активность",
      value: activity[0]?.title || "нет",
      route: "/identity/activity",
      tone: "default",
    },
    {
      id: "status",
      title: "Статус системы",
      value: health.level,
      route: "/health",
      tone: health.level === "healthy" ? "success" : "warning",
    },
    {
      id: "knowledge",
      title: "Знания",
      value: String(countKnowledge()),
      route: "/knowledge",
    },
    {
      id: "drive",
      title: "Документы",
      value: String(countDriveFiles()),
      route: "/documents",
    },
    {
      id: "calendar",
      title: "Календарь",
      value: String(countCalendarEvents()),
      route: "/calendar",
    },
    {
      id: "marketplace",
      title: "Маркетплейс",
      value: `${listInstalled().length} уст.`,
      route: "/marketplace",
    },
  ];
}
