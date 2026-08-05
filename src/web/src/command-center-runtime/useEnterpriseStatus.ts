import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useRuntimeHealth } from "@/shell/enterprise/useRuntimeHealth";
import { webConfig } from "@/config/webConfig";
import { useMemo } from "react";

export type EnterpriseStatusSnapshot = {
  environment: string;
  workspace: string;
  userLabel: string;
  runtime: string;
  gitBranch: string;
  connection: "online" | "degraded" | "offline";
  aiStatus: string;
  unread: number;
  jobs: number;
};

function detectGitBranch(): string {
  try {
    const fromEnv = import.meta.env.VITE_GIT_BRANCH as string | undefined;
    if (fromEnv) return fromEnv;
  } catch {
    /* ignore */
  }
  return import.meta.env.DEV ? "local/dev" : "main";
}

export function useEnterpriseStatus(): EnterpriseStatusSnapshot {
  const user = useAuthStore((s) => s.user);
  const workspaceId = useWorkspaceManager((s) => s.activeWorkspaceId);
  const items = useNotificationStore((s) => s.items);
  const { items: health } = useRuntimeHealth(45_000);

  return useMemo(() => {
    const unread = items.filter((i) => !i.read).length;
    const jobs = items.filter((i) => i.kind === "job" || i.kind === "workflow" || i.kind === "task").length;
    const api = health.find((h) => h.id === "api");
    const runtime = health.find((h) => h.id === "runtime");
    const ai = health.find((h) => h.id === "ai");
    let connection: EnterpriseStatusSnapshot["connection"] = "online";
    if (api?.tone === "err" || runtime?.tone === "err") connection = "offline";
    else if (api?.tone === "unknown" || api?.tone === "warn" || runtime?.tone === "unknown") connection = "degraded";

    return {
      environment: import.meta.env.DEV ? "development" : "production",
      workspace: workspaceId || "ws_default",
      userLabel: user?.name || user?.email || "Guest",
      runtime: runtime?.detail || "…",
      gitBranch: detectGitBranch(),
      connection,
      aiStatus: ai?.detail || "local",
      unread,
      jobs,
    };
  }, [user, workspaceId, items, health]);
}

export function useEnterpriseStatusLabel() {
  const s = useEnterpriseStatus();
  return `ADOS ${webConfig.version} · ${s.environment} · ${s.gitBranch}`;
}
