/**
 * Business Ecosystem Template — Sprint 30.8 / extended 30.9.
 * Extracted from Automotive reference. Shared types + platform steps.
 * Ecosystems configure domain APIs; they do not fork auth/MC/OBS/comms/concierge/AI Team.
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
  reusePercent?: number;
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
  stepId?: string;
  stepLabel?: string;
}): Promise<WorkflowStepResult> {
  return timedStep(opts.stepId || "ai_concierge", opts.stepLabel || "AI Concierge", async () => {
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
      detail: `session=${sessionId}; role=${opts.roleCustom || opts.role}`,
      data: { session: patched, preview: previewBody },
    };
  });
}

/**
 * Configure AI Team Center for an ecosystem — reuses PB /ai-team (no fork).
 * Assigns Beauty-oriented tasks to existing specialists.
 */
export async function stepAiTeamConfigure(opts: {
  organizationId: string;
  ecosystem: string;
  tasks: { label: string; task: string }[];
}): Promise<WorkflowStepResult> {
  return timedStep("ai_team", "AI Team configure", async () => {
    const org = opts.organizationId || "org_demo";
    const statusRes = await apiFetch(`${PB()}/ai-team/status`);
    const statusBody = (await statusRes.json()) as Record<string, unknown>;
    if (!statusRes.ok) throw new Error(String(statusBody.error || "AI Team status failed"));

    const dashRes = await apiFetch(
      `${PB()}/ai-team/organizations/${encodeURIComponent(org)}/dashboard`,
    );
    const dash = (await dashRes.json()) as Record<string, unknown>;
    if (!dashRes.ok) throw new Error(String(dash.error || "AI Team dashboard failed"));

    const members = Array.isArray(dash.members) ? (dash.members as Record<string, unknown>[]) : [];
    const assigned: Record<string, unknown>[] = [];
    for (let i = 0; i < opts.tasks.length; i += 1) {
      const member = members[i % Math.max(members.length, 1)];
      if (!member?.agent_id) continue;
      const actionRes = await apiFetch(
        `${PB()}/ai-team/organizations/${encodeURIComponent(org)}/actions`,
        {
          method: "POST",
          body: JSON.stringify({
            agent_id: member.agent_id,
            action: "assign_task",
            payload: {
              task: `[${opts.ecosystem}] ${opts.tasks[i].task}`,
              role_label: opts.tasks[i].label,
            },
          }),
        },
      );
      const actionBody = (await actionRes.json()) as Record<string, unknown>;
      if (!actionRes.ok) throw new Error(String(actionBody.error || "AI Team assign failed"));
      assigned.push({ label: opts.tasks[i].label, agent_id: member.agent_id, result: actionBody });
    }

    const chatRes = await apiFetch(`${PB()}/ai-team/group-chat`);
    const chatBody = chatRes.ok ? ((await chatRes.json()) as Record<string, unknown>) : {};
    return {
      detail: `AI Team ready; assigned=${assigned.length}`,
      data: { status: statusBody, dashboard: dash, assigned, group_chat: chatBody },
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
  stepId?: string;
  stepLabel?: string;
}): Promise<WorkflowStepResult> {
  return timedStep(opts.stepId || "notification", opts.stepLabel || "Notification", async () => {
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
  authentication: {
    source: "ISAM + platform JWT",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  authorization_rbac: {
    source: "ISAM roles / PermissionGuard",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  workspace: {
    source: "WorkspaceLayout + workspaceStore",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  mission_control: {
    source: "PB /mission-control",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  knowledge: {
    source: "PB knowledge / EKG",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  workflow_engine: {
    source: "ecosystem template timed steps",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  notification_system: {
    source: "enterprise-comms /center",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  telemetry: {
    source: "OBS + pilotMetrics",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  ai_platform: {
    source: "PB Concierge + AI Team",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  ui: {
    source: "EDS Button/Card/Table/Input",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  dashboards: {
    source: "domain dashboard + Pilot /pilot",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  layouts: {
    source: "WorkspaceLayout",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  shared_apis: {
    source: "comms / OBS / PB / ISAM",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  shared_components: {
    source: "EDS + ecosystem-template",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  shared_workflows: {
    source: "timedStep template",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  shared_ai: {
    source: "Concierge + AI Team + AMO",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  shared_permissions: {
    source: "ISAM RBAC + PermissionGuard",
    automotive: true,
    beauty: true,
    cafe: true,
    agriculture: true,
  },
  shared_commerce: {
    source: "ECO payments/loyalty (Beauty+Cafe); Agro uses grain marketplace",
    automotive: false,
    beauty: true,
    cafe: true,
    agriculture: false,
  },
} as const;

export type ReuseAuditResult = {
  dimensions: {
    id: string;
    source: string;
    automotive: boolean;
    beauty: boolean;
    cafe: boolean;
    agriculture: boolean;
    shared: boolean;
  }[];
  sharedCount: number;
  totalCount: number;
  reusePercent: number;
  crossEcosystemPercent: number;
};

/** Measure platform reuse — shared = all four pilots, or Beauty+Cafe commerce exception. */
export function computeReusePercentage(): ReuseAuditResult {
  const dimensions = Object.entries(ECOSYSTEM_REUSE_MATRIX).map(([id, row]) => {
    const allFour = row.automotive && row.beauty && row.cafe && row.agriculture;
    const beautyCafeCommerce = row.beauty && row.cafe && !row.automotive && !row.agriculture;
    return {
      id,
      source: row.source,
      automotive: row.automotive,
      beauty: row.beauty,
      cafe: row.cafe,
      agriculture: row.agriculture,
      shared: allFour || beautyCafeCommerce,
    };
  });
  const sharedCount = dimensions.filter((d) => d.shared).length;
  const totalCount = dimensions.length;
  const cross = dimensions.filter((d) => d.automotive && d.beauty && d.cafe && d.agriculture).length;
  return {
    dimensions,
    sharedCount,
    totalCount,
    reusePercent: totalCount ? Math.round((sharedCount / totalCount) * 1000) / 10 : 0,
    crossEcosystemPercent: totalCount ? Math.round((cross / totalCount) * 1000) / 10 : 0,
  };
}

/** Patterns validated across Automotive · Beauty · Cafe · Agriculture. */
export const CROSS_ECOSYSTEM_PATTERNS = [
  "Production auth gate (ISAM/JWT) before domain workflow",
  "Domain bootstrap → customer → primary transaction → notification",
  "PB Concierge + AI Team assign_task (no vertical AI fork)",
  "Mission Control + OBS audit/metrics at workflow end",
  "Owner dashboard + Pilot /pilot multi-ecosystem ops (Auto·Beauty·Cafe·Agro)",
  "Quality gates probe domain health + shared platform health",
  "Agriculture trade: harvest → warehouse → marketplace → export contract → sea freight",
] as const;
