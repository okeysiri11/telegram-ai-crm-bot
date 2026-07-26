/**
 * Pilot operational metrics helpers — Sprint 30.7.
 * Extends existing OBS telemetry; no parallel metrics stack.
 */

import { telemetry } from "@/integrations/telemetry";
import { apiFetch } from "@/integrations/apiClient";
import { hubIntegrations } from "@/integrations/hub";

const OBS = hubIntegrations.monitoring;

export type PilotMetricsSnapshot = {
  sessions: number;
  workflowCompletionRate: number | null;
  avgProcessingMs: number | null;
  apiResponseSamples: number;
  aiResponseSamples: number;
  errorsPerModule: Record<string, number>;
  businessEvents: number;
  systemHealthy: boolean;
  platformDash: Record<string, unknown> | null;
  businessDash: Record<string, unknown> | null;
};

const STORE_KEY = "ewp_pilot_metrics_v1";

type LocalMetrics = {
  sessions: number;
  workflowRuns: number;
  workflowSuccess: number;
  processingMs: number[];
  apiMs: number[];
  aiMs: number[];
  errorsByModule: Record<string, number>;
  businessEvents: number;
};

function loadLocal(): LocalMetrics {
  try {
    return {
      sessions: 0,
      workflowRuns: 0,
      workflowSuccess: 0,
      processingMs: [],
      apiMs: [],
      aiMs: [],
      errorsByModule: {},
      businessEvents: 0,
      ...(JSON.parse(localStorage.getItem(STORE_KEY) || "{}") as Partial<LocalMetrics>),
    };
  } catch {
    return {
      sessions: 0,
      workflowRuns: 0,
      workflowSuccess: 0,
      processingMs: [],
      apiMs: [],
      aiMs: [],
      errorsByModule: {},
      businessEvents: 0,
    };
  }
}

function saveLocal(m: LocalMetrics) {
  localStorage.setItem(STORE_KEY, JSON.stringify(m));
}

export const pilotMetrics = {
  recordSession() {
    const m = loadLocal();
    m.sessions += 1;
    saveLocal(m);
    void telemetry.sessionStart();
  },

  recordWorkflow(success: boolean, durationMs: number) {
    const m = loadLocal();
    m.workflowRuns += 1;
    if (success) m.workflowSuccess += 1;
    m.processingMs = [...m.processingMs, durationMs].slice(-50);
    saveLocal(m);
    void telemetry.businessEvent(success ? "workflow_complete" : "workflow_failed", durationMs);
    void telemetry.metric("api", durationMs, {
      event: "workflow_processing_time",
      ok: success ? "1" : "0",
    });
  },

  recordApiTiming(route: string, ms: number, ok: boolean) {
    const m = loadLocal();
    m.apiMs = [...m.apiMs, ms].slice(-100);
    saveLocal(m);
    void telemetry.apiCall(route, ms, ok);
  },

  recordAiTiming(ms: number) {
    const m = loadLocal();
    m.aiMs = [...m.aiMs, ms].slice(-50);
    saveLocal(m);
    void telemetry.metric("ai_tokens", ms, { event: "ai_response_time_ms" });
  },

  recordModuleError(module: string) {
    const m = loadLocal();
    m.errorsByModule[module] = (m.errorsByModule[module] || 0) + 1;
    saveLocal(m);
    void telemetry.error(`module_error:${module}`);
  },

  recordBusinessEvent(name: string) {
    const m = loadLocal();
    m.businessEvents += 1;
    saveLocal(m);
    void telemetry.businessEvent(name);
  },

  local(): LocalMetrics {
    return loadLocal();
  },

  async snapshot(): Promise<PilotMetricsSnapshot> {
    const local = loadLocal();
    const avg = (arr: number[]) =>
      arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : null;

    const [healthRes, platformRes, businessRes] = await Promise.all([
      apiFetch(`${OBS}/health`),
      apiFetch(`${OBS}/dashboard`, {
        method: "POST",
        body: JSON.stringify({ dashboard_type: "platform" }),
      }),
      apiFetch(`${OBS}/dashboard`, {
        method: "POST",
        body: JSON.stringify({ dashboard_type: "business" }),
      }),
    ]);

    const health = healthRes.ok ? ((await healthRes.json()) as Record<string, unknown>) : null;
    const platformDash = platformRes.ok ? ((await platformRes.json()) as Record<string, unknown>) : null;
    const businessDash = businessRes.ok ? ((await businessRes.json()) as Record<string, unknown>) : null;

    return {
      sessions: local.sessions,
      workflowCompletionRate:
        local.workflowRuns > 0
          ? Math.round((local.workflowSuccess / local.workflowRuns) * 1000) / 10
          : null,
      avgProcessingMs: avg(local.processingMs),
      apiResponseSamples: local.apiMs.length,
      aiResponseSamples: local.aiMs.length,
      errorsPerModule: { ...local.errorsByModule },
      businessEvents: local.businessEvents,
      systemHealthy: Boolean(
        health && (health.status === "ok" || health.enterprise_observability_ready),
      ),
      platformDash,
      businessDash,
    };
  },
};
