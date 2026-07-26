/**
 * Business Ecosystem Template — Sprint 30.8.
 * Extracted from Automotive reference. Shared types + platform steps.
 * Ecosystems configure domain APIs; they do not fork auth/MC/OBS/comms/concierge.
 */

import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import { hubIntegrations } from "@/integrations/hub";

export type WorkflowStepResult = {
  id: string;
  label: string;
  ok: boolean;
  durationMs: number;
  detail?: string;
  data?: Record<string, unknown>;
  error?: string;
};

export type WorkflowRunResult = {
  steps: WorkflowStepResult[];
  totalMs: number;
  success: boolean;
};

export async function timedStep(
  id: string,
  label: string,
  fn: () => Promise<{ detail?: string; data?: Record<string, unknown> }>,
): Promise<WorkflowStepResult> {
  const started = performance.now();
  try {
    const out = await fn();
    return {
      id,
      label,
      ok: true,
      durationMs: Math.round(performance.now() - started),
      detail: out.detail,
      data: out.data,
    };
  } catch (e) {
    return {
      id,
      label,
      ok: false,
      durationMs: Math.round(performance.now() - started),
      error: e instanceof Error ? e.message : String(e),
    };
  }
}

const PB = () => webConfig.platformBuilderPrefix;
const COMMS = () => webConfig.commsPrefix;
const OBS = () => hubIntegrations.monitoring;

/** Shared AI Concierge step — Platform Builder only. */
export async function stepAiConcierge(opts: {
  organizationId: string;
  name: string;
  role: string;
  roleCustom: string;
  recommendations: string[];
}): Promise<WorkflowStepResult> {
  return timedStep("ai_concierge", "AI Concierge", async () => {
    const start = await apiFetch(`${PB()}/concierge/sessions`, {
      method: "POST",
      body: JSON.stringify({ organization_id: opts.organizationId || "org_demo" }),
    });
    const session = (await start.json()) as Record<string, unknown>;
    if (!start.ok) throw new Error(String(session.error || "Concierge session failed"));
    const sessionId = String(session.session_id || "");
    const draft = {
      ...(typeof session.draft === "object" && session.draft ? (session.draft as object) : {}),
      name: opts.name,
      role: opts.role,
      role_custom: opts.roleCustom,
      recommendations: opts.recommendations,
      organization_access: ["crm", "appointments", "notifications"],
    };
    const patch = await apiFetch(`${PB()}/concierge/sessions/${sessionId}`, {
      method: "PATCH",
      body: JSON.stringify({ step: 3, draft }),
    });
    const patched = (await patch.json()) as Record<string, unknown>;
    if (!patch.ok) throw new Error(String(patched.error || "Concierge update failed"));
    const preview = await apiFetch(`${PB()}/concierge/preview`, {
      method: "POST",
      body: JSON.stringify({ draft }),
    });
    const previewBody = (await preview.json()) as Record<string, unknown>;
    return {
      detail: `session=${sessionId}`,
      data: { session: patched, preview: previewBody },
    };
  });
}

/** Shared notification via Enterprise Comms. */
export async function stepNotification(opts: {
  source: string;
  event: string;
  recipient: string;
  subject: string;
  body: string;
  payload?: Record<string, unknown>;
}): Promise<WorkflowStepResult> {
  return timedStep("notification", "Notification", async () => {
    const res = await apiFetch(`${COMMS()}/center`, {
      method: "POST",
      body: JSON.stringify({
        source: opts.source,
        event: opts.event,
        recipient: opts.recipient,
        subject: opts.subject,
        body: opts.body,
        channel: "email",
        priority: "medium",
        payload: opts.payload || {},
      }),
    });
    const body = (await res.json()) as Record<string, unknown>;
    if (!res.ok) throw new Error(String(body.error || "Notification failed"));
    return { detail: `event_id=${body.event_id}`, data: body };
  });
}

/** Shared Mission Control probe. */
export async function stepMissionControl(): Promise<WorkflowStepResult> {
  return timedStep("mission_control", "Mission Control", async () => {
    const res = await apiFetch(`${PB()}/mission-control/status`);
    const body = (await res.json()) as Record<string, unknown>;
    if (!res.ok) throw new Error(String(body.error || "Mission Control status failed"));
    const activity = await apiFetch(`${PB()}/mission-control/activity`);
    const actBody = (await activity.json()) as Record<string, unknown>;
    return {
      detail: "Mission Control status + activity probed",
      data: { status: body, activity: actBody },
    };
  });
}

/** Shared OBS audit + metric. */
export async function stepObservability(opts: {
  message: string;
  user: string;
  labels: Record<string, string>;
  stepOkCount: number;
}): Promise<WorkflowStepResult> {
  return timedStep("observability", "Observability events", async () => {
    await apiFetch(`${OBS()}/logs`, {
      method: "POST",
      body: JSON.stringify({
        kind: "audit",
        message: opts.message,
        service: "enterprise_web_platform",
        user: opts.user,
      }),
    });
    await apiFetch(`${OBS()}/metrics`, {
      method: "POST",
      body: JSON.stringify({
        kind: "api",
        value: opts.stepOkCount,
        labels: opts.labels,
      }),
    });
    return { detail: "audit log + api metric recorded" };
  });
}

/** Reuse matrix — platform capabilities every ecosystem must share. */
export const ECOSYSTEM_REUSE_MATRIX = {
  authentication: { source: "ISAM + platform JWT", automotive: true, beauty: true },
  authorization_rbac: { source: "ISAM roles / PermissionGuard", automotive: true, beauty: true },
  workspace: { source: "WorkspaceLayout + workspaceStore", automotive: true, beauty: true },
  mission_control: { source: "PB /mission-control", automotive: true, beauty: true },
  knowledge: { source: "PB knowledge / EKG", automotive: true, beauty: true },
  workflow_engine: { source: "ecosystem template timed steps", automotive: true, beauty: true },
  notification_system: { source: "enterprise-comms /center", automotive: true, beauty: true },
  telemetry: { source: "OBS + pilotMetrics", automotive: true, beauty: true },
  ai_platform: { source: "PB Concierge sessions", automotive: true, beauty: true },
  ui: { source: "EDS Button/Card/Table/Input", automotive: true, beauty: true },
  dashboards: { source: "domain dashboard + Pilot /pilot", automotive: true, beauty: true },
} as const;
