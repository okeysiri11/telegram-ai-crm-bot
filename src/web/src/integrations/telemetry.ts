/**
 * Production telemetry client — Sprint 30.4 / extended 30.5.
 * Posts to existing Enterprise Observability (/api/enterprise-obs/v1).
 * No parallel observability stack.
 */

import { hubIntegrations } from "./hub";
import { apiFetch, getIdentityContext } from "./apiClient";
import { webConfig } from "@/config/webConfig";

const OBS = hubIntegrations.monitoring;
const SERVICE = "enterprise_web_platform";

function correlationId(): string {
  return `web_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

async function postJson(path: string, body: Record<string, unknown>): Promise<void> {
  if (!webConfig.telemetryEnabled) return;
  try {
    await apiFetch(`${OBS}${path}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch {
    // Fire-and-forget — never block UI on telemetry failure
  }
}

export type ObservabilitySnapshot = {
  health: Record<string, unknown> | null;
  metrics: Record<string, unknown> | null;
  logs: Record<string, unknown> | null;
  ok: boolean;
};

export const telemetry = {
  enabled(): boolean {
    return webConfig.telemetryEnabled;
  },

  /** Structured application / audit / error / ai log */
  async log(opts: {
    kind?: "application" | "audit" | "ai" | "integration" | "security" | "error";
    message: string;
    aiAgent?: string;
    correlationId?: string;
  }): Promise<void> {
    const ctx = getIdentityContext();
    await postJson("/logs", {
      kind: opts.kind || "application",
      message: opts.message,
      service: SERVICE,
      user: ctx.email || ctx.userId || "",
      ai_agent: opts.aiAgent || "",
      correlation_id: opts.correlationId || correlationId(),
    });
  },

  async audit(action: string, detail?: string): Promise<void> {
    await this.log({
      kind: "audit",
      message: detail ? `${action}: ${detail}` : action,
    });
    try {
      const { appendAuditVault } = await import("@/audit-vault");
      const ctx = getIdentityContext();
      await appendAuditVault({
        actor: ctx.email || ctx.userId || "anonymous",
        action,
        detail,
        correlationId: correlationId(),
      });
    } catch {
      /* foundation stub must never break UX */
    }
  },

  async error(message: string, err?: Error): Promise<void> {
    await this.log({
      kind: "error",
      message: err ? `${message}: ${err.message}` : message,
    });
  },

  /** Metric kinds limited to OBS METRIC_KINDS */
  async metric(
    kind: "api" | "active_users" | "active_sessions" | "ai_tokens" | "ai_cost" | "network",
    value: number,
    labels?: Record<string, string>,
  ): Promise<void> {
    const ctx = getIdentityContext();
    await postJson("/metrics", {
      kind,
      value,
      labels: {
        service: SERVICE,
        tenant: ctx.tenantId || "",
        sprint: webConfig.sprint,
        ...labels,
      },
    });
  },

  async pageView(path: string): Promise<void> {
    await this.log({ kind: "application", message: `page_view ${path}` });
    await this.metric("api", 1, { event: "page_view", path });
  },

  async sessionStart(): Promise<void> {
    await this.metric("active_sessions", 1, { event: "session_start" });
    await this.audit("session_start", getIdentityContext().tenantId || "anonymous");
  },

  async userActivity(action: string): Promise<void> {
    await this.log({ kind: "application", message: `user_activity ${action}` });
    await this.metric("active_users", 1, { event: action });
  },

  async aiActivity(agent: string, detail: string): Promise<void> {
    await this.log({ kind: "ai", message: detail, aiAgent: agent });
    await this.metric("ai_tokens", 0, { agent, event: "ai_activity" });
  },

  async apiCall(route: string, durationMs: number, ok: boolean): Promise<void> {
    await this.metric("api", durationMs, {
      route,
      status: ok ? "ok" : "error",
    });
  },

  /** Business metric helper — uses active_users kind with business labels. */
  async businessEvent(event: string, value = 1): Promise<void> {
    await this.log({ kind: "application", message: `business_event ${event}` });
    await this.metric("active_users", value, { event, scope: "business" });
  },

  /** Pull health snapshot from existing OBS endpoints (central monitoring). */
  async healthSnapshot(): Promise<ObservabilitySnapshot> {
    try {
      const [h, m, l] = await Promise.all([
        apiFetch(`${OBS}/health`),
        apiFetch(`${OBS}/metrics`),
        apiFetch(`${OBS}/logs`),
      ]);
      const health = h.ok ? ((await h.json()) as Record<string, unknown>) : null;
      const metrics = m.ok ? ((await m.json()) as Record<string, unknown>) : null;
      const logs = l.ok ? ((await l.json()) as Record<string, unknown>) : null;
      return { health, metrics, logs, ok: Boolean(health) };
    } catch {
      return { health: null, metrics: null, logs: null, ok: false };
    }
  },
};
