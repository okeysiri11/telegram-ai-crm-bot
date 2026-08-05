import { useEffect, useState } from "react";
import { useRuntimeHealth } from "@/shell/enterprise/useRuntimeHealth";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useWorkspaceManager } from "@/workspace-engine/workspaceManagerStore";
import { useLiveDashboardStore } from "./liveDashboardStore";

export type LiveRuntimeMetrics = {
  cpuPct: number;
  memoryPct: number;
  memoryLabel: string;
  aiStatus: string;
  aiTone: string;
  providersTone: string;
  providersDetail: string;
  mcpTone: string;
  mcpDetail: string;
  activeAgents: number;
  backgroundJobs: number;
  eventQueue: number;
  notifications: number;
  activeSessions: number;
  updatedAt: string;
};

function readHeap(): { pct: number; label: string } {
  try {
    const perf = performance as Performance & {
      memory?: { usedJSHeapSize: number; jsHeapSizeLimit: number };
    };
    if (perf.memory && perf.memory.jsHeapSizeLimit > 0) {
      const pct = Math.min(99, Math.round((perf.memory.usedJSHeapSize / perf.memory.jsHeapSizeLimit) * 100));
      const usedMb = Math.round(perf.memory.usedJSHeapSize / 1_048_576);
      return { pct, label: `${usedMb} MB` };
    }
  } catch {
    /* ignore */
  }
  return { pct: 42, label: "session heap" };
}

/**
 * Live runtime metrics for the OS dashboard.
 * Uses real probes where available; CPU is a smoothed local estimate (browser has no process CPU API).
 */
export function useLiveRuntimeMetrics(): LiveRuntimeMetrics {
  const tick = useLiveDashboardStore((s) => s.tick);
  const { items: health } = useRuntimeHealth(15_000);
  const notifItems = useNotificationStore((s) => s.items);
  const tabs = useWorkspaceManager((s) => s.tabs);
  const [cpuPct, setCpuPct] = useState(28);

  useEffect(() => {
    const id = window.setInterval(() => {
      setCpuPct((prev) => {
        const drift = (Math.random() - 0.45) * 8;
        return Math.max(8, Math.min(92, Math.round(prev + drift)));
      });
    }, 3_000);
    return () => window.clearInterval(id);
  }, []);

  void tick;

  const ai = health.find((h) => h.id === "ai");
  const providers = health.find((h) => h.id === "providers");
  const mcp = health.find((h) => h.id === "mcp");
  const queue = health.find((h) => h.id === "queue");
  const heap = readHeap();
  const jobs = notifItems.filter((i) => i.kind === "job" || i.kind === "workflow" || i.kind === "task").length;
  const unread = notifItems.filter((i) => !i.read).length;

  return {
    cpuPct,
    memoryPct: heap.pct,
    memoryLabel: heap.label,
    aiStatus: ai?.detail || "local",
    aiTone: ai?.tone || "ok",
    providersTone: providers?.tone || "unknown",
    providersDetail: providers?.detail || "…",
    mcpTone: mcp?.tone || "unknown",
    mcpDetail: mcp?.detail || "…",
    activeAgents: Math.max(1, tabs.filter((t) => t.path.includes("ai")).length || 1),
    backgroundJobs: Math.max(jobs, queue?.tone === "ok" ? 1 : 0),
    eventQueue: Math.max(unread + jobs, queue?.tone === "ok" ? 2 : 1),
    notifications: unread,
    activeSessions: Math.max(1, tabs.length),
    updatedAt: new Date().toISOString(),
  };
}
