/**
 * Automotive live workflow API helpers — Sprint 30.6.
 * Calls existing /api/auto/v1, platform-builder concierge, enterprise-comms, mission-control.
 */

import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import { hubIntegrations } from "@/integrations/hub";

const AUTO = webConfig.autoPrefix;
const PB = webConfig.platformBuilderPrefix;
const COMMS = webConfig.commsPrefix;

export type WorkflowStepResult = {
  id: string;
  label: string;
  ok: boolean;
  durationMs: number;
  detail?: string;
  data?: Record<string, unknown>;
  error?: string;
};

async function timed<T>(
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

export async function runAutomotiveLiveWorkflow(opts: {
  customerEmail: string;
  customerPassword: string;
  firstName: string;
  lastName: string;
  organizationId: string;
}): Promise<{ steps: WorkflowStepResult[]; totalMs: number; success: boolean }> {
  const steps: WorkflowStepResult[] = [];
  const wall = performance.now();
  let customerId = "";
  let leadId = "";
  let nba = "";
  let conciergeSessionId = "";

  steps.push(
    await timed("customer_auth", "Customer authentication (portal)", async () => {
      // Try register; on conflict, login
      let res = await apiFetch(`${AUTO}/portal/auth/register`, {
        method: "POST",
        body: JSON.stringify({
          email: opts.customerEmail,
          password: opts.customerPassword,
          first_name: opts.firstName,
          last_name: opts.lastName,
        }),
      });
      let body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) {
        res = await apiFetch(`${AUTO}/portal/auth/login`, {
          method: "POST",
          body: JSON.stringify({
            email: opts.customerEmail,
            password: opts.customerPassword,
          }),
        });
        body = (await res.json()) as Record<string, unknown>;
        if (!res.ok) throw new Error(String(body.error || "Portal auth failed"));
      }
      const user = (body.user || {}) as Record<string, unknown>;
      const token = (body.token || {}) as Record<string, unknown>;
      customerId = String(user.customer_id || "");
      return {
        detail: `user=${user.user_id}; customer=${customerId}`,
        data: { user, token },
      };
    }),
  );

  steps.push(
    await timed("dashboard", "Automotive dashboard", async () => {
      const res = await apiFetch(`${AUTO}/dashboard`);
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "Dashboard failed"));
      return { detail: "dashboard loaded", data: body };
    }),
  );

  steps.push(
    await timed("crm_customer", "CRM customer", async () => {
      if (customerId) {
        return { detail: `reused portal customer ${customerId}`, data: { customer_id: customerId } };
      }
      const res = await apiFetch(`${AUTO}/crm/customers`, {
        method: "POST",
        body: JSON.stringify({
          first_name: opts.firstName,
          last_name: opts.lastName,
          email: opts.customerEmail,
          phone: "+10000000000",
          preferences: { source: "pilot_workflow_30_6" },
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "CRM customer failed"));
      customerId = String(body.customer_id || "");
      return { detail: `customer_id=${customerId}`, data: body };
    }),
  );

  steps.push(
    await timed("crm_lead", "CRM lead", async () => {
      const res = await apiFetch(`${AUTO}/crm/leads`, {
        method: "POST",
        body: JSON.stringify({
          customer_id: customerId,
          vehicle_id: "veh_pilot_demo",
          dealer_id: "dealer_pilot",
          source: "web",
          notes: "Sprint 30.6 first live Automotive workflow",
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "CRM lead failed"));
      leadId = String(body.lead_id || "");
      const nbaObj = body.next_best_action as Record<string, unknown> | string | undefined;
      nba =
        typeof nbaObj === "string"
          ? nbaObj
          : String((nbaObj as Record<string, unknown>)?.action || JSON.stringify(nbaObj || {}));
      return { detail: `lead_id=${leadId}; nba=${nba}`, data: body };
    }),
  );

  steps.push(
    await timed("ai_concierge", "AI Concierge + routing", async () => {
      const start = await apiFetch(`${PB}/concierge/sessions`, {
        method: "POST",
        body: JSON.stringify({ organization_id: opts.organizationId || "org_demo" }),
      });
      const session = (await start.json()) as Record<string, unknown>;
      if (!start.ok) throw new Error(String(session.error || "Concierge session failed"));
      conciergeSessionId = String(session.session_id || "");

      const draft = {
        ...(typeof session.draft === "object" && session.draft ? (session.draft as object) : {}),
        name: "Automotive Pilot Concierge",
        role: "business_concierge",
        role_custom: "Automotive lead follow-up",
        recommendations: [nba || "Follow up lead", `lead:${leadId}`],
        organization_access: ["crm", "leads", "notifications"],
      };
      const patch = await apiFetch(`${PB}/concierge/sessions/${conciergeSessionId}`, {
        method: "PATCH",
        body: JSON.stringify({
          step: 3,
          draft,
        }),
      });
      const patched = (await patch.json()) as Record<string, unknown>;
      if (!patch.ok) throw new Error(String(patched.error || "Concierge update failed"));

      const preview = await apiFetch(`${PB}/concierge/preview`, {
        method: "POST",
        body: JSON.stringify({ draft }),
      });
      const previewBody = (await preview.json()) as Record<string, unknown>;

      return {
        detail: `session=${conciergeSessionId}; nba_context=${nba}`,
        data: { session: patched, preview: previewBody, next_best_action: nba },
      };
    }),
  );

  steps.push(
    await timed("task", "Task creation", async () => {
      const res = await apiFetch(`${AUTO}/crm/tasks`, {
        method: "POST",
        body: JSON.stringify({
          title: nba ? `NBA: ${nba}` : "Follow up Automotive lead",
          description: `Pilot workflow task for lead ${leadId} / customer ${customerId}`,
          customer_id: customerId,
          lead_id: leadId,
          assigned_agent_id: "agent_pilot",
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "Task create failed"));
      return { detail: `task_id=${body.task_id}`, data: body };
    }),
  );

  steps.push(
    await timed("notification", "Notification", async () => {
      const res = await apiFetch(`${COMMS}/center`, {
        method: "POST",
        body: JSON.stringify({
          source: "automotive_pilot_workflow",
          event: "lead_created",
          recipient: opts.customerEmail,
          subject: "Your Automotive inquiry",
          body: `Lead ${leadId} received. Next action: ${nba || "follow-up"}`,
          channel: "email",
          priority: "medium",
          payload: { lead_id: leadId, customer_id: customerId, concierge: conciergeSessionId },
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "Notification failed"));
      return { detail: `event_id=${body.event_id}`, data: body };
    }),
  );

  steps.push(
    await timed("mission_control", "Mission Control live status", async () => {
      const res = await apiFetch(`${PB}/mission-control/status`);
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "Mission Control status failed"));
      const activity = await apiFetch(`${PB}/mission-control/activity`);
      const actBody = (await activity.json()) as Record<string, unknown>;
      return {
        detail: "Mission Control status + activity probed",
        data: { status: body, activity: actBody },
      };
    }),
  );

  steps.push(
    await timed("analytics", "Analytics / pipeline", async () => {
      const [dash, pipe, bi] = await Promise.all([
        apiFetch(`${AUTO}/dashboard`),
        apiFetch(`${AUTO}/crm/pipeline`),
        apiFetch(`${AUTO}/bi/dashboard`),
      ]);
      const dashBody = (await dash.json()) as Record<string, unknown>;
      const pipeBody = (await pipe.json()) as Record<string, unknown>;
      const biBody = bi.ok ? ((await bi.json()) as Record<string, unknown>) : {};
      if (!dash.ok) throw new Error(String(dashBody.error || "Analytics dashboard failed"));
      return {
        detail: "dashboard + pipeline + bi loaded",
        data: { dashboard: dashBody, pipeline: pipeBody, bi: biBody },
      };
    }),
  );

  steps.push(
    await timed("observability", "Observability events", async () => {
      const obs = hubIntegrations.monitoring;
      await apiFetch(`${obs}/logs`, {
        method: "POST",
        body: JSON.stringify({
          kind: "audit",
          message: `automotive_workflow_complete lead=${leadId}`,
          service: "enterprise_web_platform",
          user: opts.customerEmail,
        }),
      });
      await apiFetch(`${obs}/metrics`, {
        method: "POST",
        body: JSON.stringify({
          kind: "api",
          value: steps.filter((s) => s.ok).length,
          labels: { event: "automotive_workflow", lead_id: leadId },
        }),
      });
      return { detail: "audit log + api metric recorded" };
    }),
  );

  const success = steps.every((s) => s.ok);
  return { steps, totalMs: Math.round(performance.now() - wall), success };
}
