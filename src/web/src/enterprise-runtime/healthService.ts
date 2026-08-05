/**
 * Health Service singleton — Sprint 28.1.
 * ONE probe loop for the whole OS. Consumers subscribe; no per-hook polling.
 */

import {
  STATUS_PROBES,
  type StatusTone,
} from "@/shell/enterprise/statusCatalog";
import {
  aggregateHealth,
  HEALTH_POLL_MS,
  toneToHealth,
  type HealthLevel,
  type RuntimeHealthId,
  type RuntimeHealthItem,
} from "./types";

type Listener = (items: RuntimeHealthItem[], level: HealthLevel, at: string) => void;

const listeners = new Set<Listener>();
let items: RuntimeHealthItem[] = seedItems();
let level: HealthLevel = "offline";
let updatedAt: string | null = null;
let timer: number | null = null;
let started = false;
let busy = false;
let refCount = 0;

function seedItems(): RuntimeHealthItem[] {
  const extras: RuntimeHealthItem[] = [
    { id: "frontend", label: "Frontend", tone: "ok", detail: import.meta.env.DEV ? "dev" : "production" },
    { id: "ai", label: "AI", tone: "ok", detail: "local ready" },
    { id: "memory", label: "Memory", tone: "ok", detail: "browser session" },
  ];
  const probes = STATUS_PROBES.map((p) => ({
    id: p.id as RuntimeHealthId,
    label: p.label,
    tone: (p.staticTone || "unknown") as StatusTone,
    detail: p.staticDetail || "…",
  }));
  return [...extras, ...probes];
}

async function softProbe(url: string, signal: AbortSignal): Promise<StatusTone> {
  try {
    const res = await fetch(url, { signal, credentials: "same-origin" });
    if (res.ok) return "ok";
    if (res.status >= 500) return "err";
    return "warn";
  } catch {
    return "unknown";
  }
}

function detailFor(tone: StatusTone, staticDetail?: string): string {
  if (staticDetail) return staticDetail;
  if (tone === "ok") return "online";
  if (tone === "warn") return "degraded";
  if (tone === "err") return "error";
  return "offline (local)";
}

function emit() {
  listeners.forEach((l) => l(items, level, updatedAt || new Date().toISOString()));
}

async function refresh() {
  if (busy || typeof window === "undefined") return;
  if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
  busy = true;
  const ctrl = new AbortController();
  const abortTimer = window.setTimeout(() => ctrl.abort(), 2500);
  try {
    const probed = await Promise.all(
      STATUS_PROBES.map(async (p) => {
        if (!p.healthUrl) {
          return {
            id: p.id as RuntimeHealthId,
            label: p.label,
            tone: (p.staticTone || "ok") as StatusTone,
            detail: p.staticDetail || "ready",
          } satisfies RuntimeHealthItem;
        }
        const tone = await softProbe(p.healthUrl, ctrl.signal);
        return {
          id: p.id as RuntimeHealthId,
          label: p.label,
          tone,
          detail: detailFor(tone),
        } satisfies RuntimeHealthItem;
      }),
    );
    const aiTone = probed.find((p) => p.id === "providers")?.tone || "unknown";
    const extras: RuntimeHealthItem[] = [
      { id: "frontend", label: "Frontend", tone: "ok", detail: import.meta.env.DEV ? "dev" : "production" },
      {
        id: "ai",
        label: "AI",
        tone: aiTone === "ok" ? "ok" : aiTone === "unknown" ? "ok" : aiTone,
        detail: aiTone === "ok" ? "providers online" : "local fallback",
      },
      {
        id: "memory",
        label: "Memory",
        tone: "ok",
        detail:
          typeof performance !== "undefined" && "memory" in performance ? "heap tracked" : "session ok",
      },
    ];
    items = [...extras, ...probed];
    level = aggregateHealth(items);
    updatedAt = new Date().toISOString();
    emit();
  } finally {
    window.clearTimeout(abortTimer);
    busy = false;
  }
}

function ensureTimer() {
  if (timer != null || typeof window === "undefined") return;
  timer = window.setInterval(() => void refresh(), HEALTH_POLL_MS);
}

function clearTimer() {
  if (timer == null) return;
  window.clearInterval(timer);
  timer = null;
}

export const healthService = {
  /** Acquire shared poller (ref-counted). */
  start() {
    refCount += 1;
    if (started) return;
    started = true;
    void refresh();
    ensureTimer();
  },

  stop() {
    refCount = Math.max(0, refCount - 1);
    if (refCount > 0) return;
    clearTimer();
    started = false;
  },

  subscribe(listener: Listener) {
    listeners.add(listener);
    listener(items, level, updatedAt || new Date().toISOString());
    this.start();
    return () => {
      listeners.delete(listener);
      this.stop();
    };
  },

  getItems() {
    return items;
  },

  getLevel() {
    return level;
  },

  getUpdatedAt() {
    return updatedAt;
  },

  async refresh() {
    await refresh();
    return items;
  },

  levelForId(id: RuntimeHealthId): HealthLevel {
    const hit = items.find((i) => i.id === id);
    return hit ? toneToHealth(hit.tone) : "offline";
  },
};
