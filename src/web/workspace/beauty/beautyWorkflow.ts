/**
 * Beauty live workflow — Sprint 30.8.
 * Uses existing BOS / BWS / BCJ APIs + shared ecosystem template (auth/MC/comms/OBS/concierge).
 * Does not fork Automotive or duplicate platform services.
 */

import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import { hubIntegrations } from "@/integrations/hub";
import {
  timedStep,
  stepAiConcierge,
  stepNotification,
  stepMissionControl,
  stepObservability,
  type WorkflowRunResult,
  type WorkflowStepResult,
} from "../ecosystem-template";

const BOS = () => webConfig.beautyOsPrefix;
const BWS = () => webConfig.beautyWorkspacePrefix;
const BCJ = () => webConfig.beautyClientJourneyPrefix;
const AMO = () => webConfig.aiMarketingOsPrefix;

export type { WorkflowStepResult };

export async function runBeautyLiveWorkflow(opts: {
  clientName: string;
  clientEmail: string;
  organizationId: string;
}): Promise<WorkflowRunResult> {
  const steps: WorkflowStepResult[] = [];
  const wall = performance.now();

  let companyId = "";
  let branchId = "";
  let customerId = "";
  let serviceId = "";
  let employeeId = "";
  let appointmentId = "";
  let bookingId = "";

  steps.push(
    await timedStep("staff_auth", "Staff authentication (session)", async () => {
      return {
        detail: "Staff JWT/ISAM session required by ProtectedRoute + validateSession",
        data: { gate: "production_auth" },
      };
    }),
  );

  steps.push(
    await timedStep("bootstrap", "Salon CRM bootstrap (BOS)", async () => {
      const res = await apiFetch(`${BOS()}/bootstrap`, {
        method: "POST",
        body: "{}",
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "BOS bootstrap failed"));
      companyId = String(body.company_id || "");
      branchId = String(body.branch_id || "");
      return {
        detail: `company=${companyId}; branch=${branchId}`,
        data: body,
      };
    }),
  );

  steps.push(
    await timedStep("client", "Client (CRM customer)", async () => {
      const res = await apiFetch(`${BOS()}/customers`, {
        method: "POST",
        body: JSON.stringify({
          name: opts.clientName,
          preferences: ["pilot_30_8", opts.clientEmail],
          allergies: [],
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "BOS customer failed"));
      customerId = String(body.customer_id || "");
      return { detail: `customer_id=${customerId}`, data: body };
    }),
  );

  steps.push(
    await timedStep("services_employees", "Services + employees", async () => {
      const svc = await apiFetch(`${BOS()}/services`, {
        method: "POST",
        body: JSON.stringify({
          name: "Pilot Haircut",
          category: "hair",
          duration_min: 45,
          price: 40,
          description: "Sprint 30.8 beauty pilot service",
        }),
      });
      const svcBody = (await svc.json()) as Record<string, unknown>;
      if (!svc.ok) throw new Error(String(svcBody.error || "BOS service failed"));
      serviceId = String(svcBody.service_id || "");

      const emp = await apiFetch(`${BOS()}/employees`, {
        method: "POST",
        body: JSON.stringify({
          name: "Pilot Stylist",
          role: "stylist",
          specialization: "hair",
          services: ["Pilot Haircut"],
        }),
      });
      const empBody = (await emp.json()) as Record<string, unknown>;
      if (!emp.ok) throw new Error(String(empBody.error || "BOS employee failed"));
      employeeId = String(empBody.employee_id || "");
      return {
        detail: `service=${serviceId}; employee=${employeeId}`,
        data: { service: svcBody, employee: empBody },
      };
    }),
  );

  steps.push(
    await timedStep("appointment", "Appointment booking", async () => {
      const start = new Date(Date.now() + 3600_000).toISOString();
      const end = new Date(Date.now() + 7200_000).toISOString();
      const book = await apiFetch(`${BCJ()}/book`, {
        method: "POST",
        body: JSON.stringify({
          channel: "online",
          customer_id: customerId,
          service_ids: [serviceId || "Pilot Haircut"],
          employee_id: employeeId,
          branch_id: branchId || "auto:branch",
          start,
          end,
          auto_pick: true,
          duration_min: 45,
        }),
      });
      const bookBody = (await book.json()) as Record<string, unknown>;
      if (!book.ok) {
        const appt = await apiFetch(`${BOS()}/appointments`, {
          method: "POST",
          body: JSON.stringify({
            customer_id: customerId,
            service_id: serviceId,
            employee_id: employeeId,
            branch_id: branchId,
            start,
            end,
          }),
        });
        const apptBody = (await appt.json()) as Record<string, unknown>;
        if (!appt.ok) throw new Error(String(bookBody.error || apptBody.error || "Appointment failed"));
        appointmentId = String(apptBody.appointment_id || "");
        return { detail: `appointment_id=${appointmentId} (BOS)`, data: apptBody };
      }
      appointmentId = String(bookBody.appointment_id || "");
      bookingId = String(bookBody.booking_id || "");
      return {
        detail: `booking=${bookingId}; appointment=${appointmentId}`,
        data: bookBody,
      };
    }),
  );

  steps.push(
    await timedStep("calendar", "Calendar / schedule (BWS)", async () => {
      const bwsBoot = await apiFetch(`${BWS()}/bootstrap`, { method: "POST", body: "{}" });
      if (!bwsBoot.ok) {
        const err = (await bwsBoot.json()) as Record<string, unknown>;
        throw new Error(String(err.error || "BWS bootstrap failed"));
      }
      const res = await apiFetch(`${BWS()}/schedule?view=day`);
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) {
        const post = await apiFetch(`${BWS()}/schedule`, {
          method: "POST",
          body: JSON.stringify({ view: "day" }),
        });
        const postBody = (await post.json()) as Record<string, unknown>;
        if (!post.ok) throw new Error(String(body.error || postBody.error || "Schedule failed"));
        return { detail: "schedule day view (POST)", data: postBody };
      }
      return { detail: "schedule day view", data: body };
    }),
  );

  steps.push(
    await timedStep("ai_reminder", "AI reminder / booking assistant", async () => {
      const res = await apiFetch(`${BCJ()}/assistant`, {
        method: "POST",
        body: JSON.stringify({
          service_ids: [serviceId || "Pilot Haircut"],
          customer_id: customerId,
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "BCJ assistant failed"));
      const notes = await apiFetch(`${BWS()}/notifications`);
      const noteBody = notes.ok ? ((await notes.json()) as Record<string, unknown>) : {};
      return { detail: "booking assistant + workspace notifications", data: { assistant: body, notifications: noteBody } };
    }),
  );

  steps.push(
    await timedStep("crm_update", "CRM journey update", async () => {
      const res = await apiFetch(`${BCJ()}/journey`, {
        method: "POST",
        body: JSON.stringify({
          customer_id: customerId,
          source: "pilot_30_8",
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "BCJ journey failed"));
      return { detail: `journey_id=${body.journey_id}`, data: body };
    }),
  );

  steps.push(
    await stepAiConcierge({
      organizationId: opts.organizationId,
      name: "Beauty Pilot Concierge",
      role: "business_concierge",
      roleCustom: "Beauty appointment follow-up",
      recommendations: [
        `appointment:${appointmentId || bookingId}`,
        `customer:${customerId}`,
        "Confirm appointment reminder",
      ],
    }),
  );

  steps.push(
    await timedStep("marketing", "AI Marketing (AMO probe)", async () => {
      const health = await apiFetch(`${AMO()}/health`);
      const healthBody = (await health.json()) as Record<string, unknown>;
      if (!health.ok) throw new Error(String(healthBody.error || "AMO health failed"));
      const boot = await apiFetch(`${AMO()}/bootstrap`, { method: "POST", body: "{}" });
      const bootBody = boot.ok ? ((await boot.json()) as Record<string, unknown>) : {};
      return {
        detail: "AMO health + bootstrap (shared AI Marketing OS)",
        data: { health: healthBody, bootstrap: bootBody },
      };
    }),
  );

  steps.push(
    await timedStep("owner_dashboard", "Owner dashboard (BOS)", async () => {
      const res = await apiFetch(`${BOS()}/dashboard`);
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "BOS dashboard failed"));
      const bwsDash = await apiFetch(`${BWS()}/dashboard`);
      const bwsBody = bwsDash.ok ? ((await bwsDash.json()) as Record<string, unknown>) : {};
      return {
        detail: "BOS + BWS dashboards",
        data: { bos: body, bws: bwsBody },
      };
    }),
  );

  steps.push(await stepMissionControl());

  steps.push(
    await timedStep("analytics", "Analytics", async () => {
      const [bos, bws] = await Promise.all([
        apiFetch(`${BOS()}/dashboard`),
        apiFetch(`${BWS()}/dashboard`),
      ]);
      const bosBody = (await bos.json()) as Record<string, unknown>;
      const bwsBody = bws.ok ? ((await bws.json()) as Record<string, unknown>) : {};
      if (!bos.ok) throw new Error(String(bosBody.error || "Analytics failed"));
      return { detail: "beauty analytics surfaces", data: { bos: bosBody, bws: bwsBody } };
    }),
  );

  steps.push(
    await stepNotification({
      source: "beauty_pilot_workflow",
      event: "appointment_booked",
      recipient: opts.clientEmail,
      subject: "Your Beauty appointment",
      body: `Appointment ${appointmentId || bookingId} confirmed for ${opts.clientName}`,
      payload: {
        appointment_id: appointmentId,
        booking_id: bookingId,
        customer_id: customerId,
        company_id: companyId,
      },
    }),
  );

  steps.push(
    await timedStep("quality_gates", "Quality gates (BOS/BWS/BCJ/OBS)", async () => {
      const probes = await Promise.all([
        apiFetch(`${BOS()}/health`),
        apiFetch(`${BWS()}/health`),
        apiFetch(`${BCJ()}/health`),
        apiFetch(`${hubIntegrations.monitoring}/health`),
      ]);
      const labels = ["bos", "bws", "bcj", "obs"];
      const results: Record<string, boolean> = {};
      for (let i = 0; i < probes.length; i += 1) results[labels[i]] = probes[i].ok;
      if (!Object.values(results).every(Boolean)) {
        throw new Error(`Quality gate failures: ${JSON.stringify(results)}`);
      }
      return { detail: "BOS · BWS · BCJ · OBS healthy", data: results };
    }),
  );

  steps.push(
    await stepObservability({
      message: `beauty_workflow_complete appointment=${appointmentId || bookingId}`,
      user: opts.clientEmail,
      labels: {
        event: "beauty_workflow",
        appointment_id: appointmentId || bookingId,
        ecosystem: "beauty",
      },
      stepOkCount: steps.filter((s) => s.ok).length,
    }),
  );

  const success = steps.every((s) => s.ok);
  return { steps, totalMs: Math.round(performance.now() - wall), success };
}
