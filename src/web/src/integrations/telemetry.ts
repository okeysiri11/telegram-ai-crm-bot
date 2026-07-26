/**
 * Production telemetry client — Sprint 30.4.
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
};
