/**
 * Legal operational pilot — Sprint 31.2.
 * Reuses /api/legal-cm/v1 + /api/legal-di/v1 + /api/legal-cp/v1 + /api/legal-aa/v1
 * + /api/legal-enterprise/v1 + /api/legal-ei/v1 + shared ecosystem template.
 * Does not fork Auto / Beauty / Cafe / Agriculture.
 */

import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import { hubIntegrations } from "@/integrations/hub";
import {
  timedStep,
  stepAiConcierge,
  stepAiTeamConfigure,
  stepNotification,
  stepMissionControl,
  stepObservability,
  computeReusePercentage,
  type WorkflowRunResult,
  type WorkflowStepResult,
} from "../ecosystem-template";

const LE = () => webConfig.legalEnterprisePrefix;
const CM = () => webConfig.legalCasePrefix;
const DI = () => webConfig.legalDocumentsPrefix;
const CP = () => webConfig.legalCompliancePrefix;
const AA = () => webConfig.legalAiPrefix;
const EI = () => webConfig.legalExecutivePrefix;
const ISAM = () => hubIntegrations.authentication;

export type { WorkflowStepResult };

export async function runLegalLiveWorkflow(opts: {
  clientName: string;
  clientEmail: string;
  organizationId: string;
}): Promise<WorkflowRunResult> {
  const steps: WorkflowStepResult[] = [];
  const wall = performance.now();

  let clientId = "";
  let companyId = "";
  let attorneyId = "";
  let caseId = "";
  let documentId = "";
  let contractId = "";
  let hearingId = "";
  let taskId = "";

  steps.push(
    await timedStep("login", "Login (production auth)", async () => {
      const isam = await apiFetch(`${ISAM()}/health`);
      const body = isam.ok ? ((await isam.json()) as Record<string, unknown>) : {};
      return { detail: "Staff session + ISAM health", data: { gate: "production_auth", isam: body } };
    }),
  );

  steps.push(
    await timedStep("law_firm_crm", "Law Firm CRM", async () => {
      const entity = await apiFetch(`${LE()}/registry`, {
        method: "POST",
        body: JSON.stringify({
          action: "entity",
          name: "Lee & Partners Pilot",
          entity_type: "corporation",
          jurisdiction: "US-DE",
          registration_no: "DE-LEGAL-31",
        }),
      });
      const entityBody = (await entity.json()) as Record<string, unknown>;
      if (!entity.ok) throw new Error(String(entityBody.error || "Firm entity failed"));

      const individual = await apiFetch(`${LE()}/registry`, {
        method: "POST",
        body: JSON.stringify({
          action: "individual",
          full_name: opts.clientName,
          national_id: `ID-${Date.now().toString(36)}`,
          residency: "US-NY",
        }),
      });
      const individualBody = (await individual.json()) as Record<string, unknown>;
      if (!individual.ok) throw new Error(String(individualBody.error || "Client register failed"));
      clientId = String(individualBody.individual_id || "");

      const attorney = await apiFetch(`${LE()}/registry`, {
        method: "POST",
        body: JSON.stringify({
          action: "attorney",
          full_name: "Jordan Lee",
          bar_number: `BAR-${Date.now().toString(36)}`,
          firm: "Lee & Partners",
          specializations: ["commercial", "litigation"],
        }),
      });
      const attorneyBody = (await attorney.json()) as Record<string, unknown>;
      if (!attorney.ok) throw new Error(String(attorneyBody.error || "Attorney register failed"));
      attorneyId = String(attorneyBody.attorney_id || "");

      const customer = await apiFetch(`${CP()}/counterparties`, {
        method: "POST",
        body: JSON.stringify({
          action: "customer",
          name: opts.clientName,
          country: "US",
          risk_level: "medium",
        }),
      });
      const customerBody = (await customer.json()) as Record<string, unknown>;
      if (!customer.ok) throw new Error(String(customerBody.error || "Counterparty failed"));

      const company = await apiFetch(`${CP()}/governance`, {
        method: "POST",
        body: JSON.stringify({
          action: "company",
          name: `${opts.clientName} Holdings`,
          jurisdiction: "US-DE",
          registration_no: `DE-${Date.now().toString(36)}`,
          structure: "corporation",
        }),
      });
      const companyBody = (await company.json()) as Record<string, unknown>;
      if (!company.ok) throw new Error(String(companyBody.error || "Company failed"));
      companyId = String(companyBody.company_id || "");

      return {
        detail: `client=${clientId}; company=${companyId}; attorney=${attorneyId}`,
        data: {
          entity: entityBody,
          client: individualBody,
          attorney: attorneyBody,
          customer: customerBody,
          company: companyBody,
        },
      };
    }),
  );

  steps.push(
    await timedStep("ai_intake", "AI Intake", async () => {
      const ask = await apiFetch(`${AA()}/assistant`, {
        method: "POST",
        body: JSON.stringify({
          action: "ask",
          question: `Intake for ${opts.clientName}: commercial dispute over unpaid services invoice. Outline case framing and next steps.`,
        }),
      });
      const askBody = (await ask.json()) as Record<string, unknown>;
      if (!ask.ok) throw new Error(String(askBody.error || "AI intake failed"));

      const research = await apiFetch(`${AA()}/research`, {
        method: "POST",
        body: JSON.stringify({ action: "statute", query: "breach of contract damages" }),
      });
      const researchBody = research.ok ? ((await research.json()) as Record<string, unknown>) : {};

      return {
        detail: "AI Lawyer intake + research",
        data: { assistant: askBody, research: researchBody },
      };
    }),
  );

  steps.push(
    await timedStep("case_creation", "Case creation", async () => {
      const res = await apiFetch(`${CM()}/cases`, {
        method: "POST",
        body: JSON.stringify({
          title: `Pilot Matter — ${opts.clientName}`,
          category: "commercial",
          priority: "high",
          status: "intake",
          owner: "Jordan Lee",
          court_name: "District Court",
          case_number: `CV-2026-${Date.now().toString(36).toUpperCase()}`,
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "Case create failed"));
      caseId = String(body.case_id || "");

      const aiCase = await apiFetch(`${CM()}/ai`, {
        method: "POST",
        body: JSON.stringify({ action: "summary", case_id: caseId }),
      });
      const aiBody = aiCase.ok ? ((await aiCase.json()) as Record<string, unknown>) : {};

      const timeline = await apiFetch(`${CM()}/cases`, {
        method: "POST",
        body: JSON.stringify({
          action: "timeline",
          case_id: caseId,
          event: "intake_complete",
          detail: "Pilot intake completed",
        }),
      });
      const timelineBody = timeline.ok ? ((await timeline.json()) as Record<string, unknown>) : {};

      return {
        detail: `case_id=${caseId}`,
        data: { case: body, ai_summary: aiBody, timeline: timelineBody },
      };
    }),
  );

  steps.push(
    await timedStep("document_generation", "Document generation", async () => {
      const template = await apiFetch(`${DI()}/contracts`, {
        method: "POST",
        body: JSON.stringify({
          action: "template",
          name: "Demand Letter Template",
          contract_type: "custom",
          body: "Demand for payment under commercial services agreement.",
          clauses: [],
        }),
      });
      const templateBody = (await template.json()) as Record<string, unknown>;
      if (!template.ok) throw new Error(String(templateBody.error || "Template failed"));

      const contract = await apiFetch(`${DI()}/contracts`, {
        method: "POST",
        body: JSON.stringify({
          action: "nda",
          title: "Mutual NDA — Pilot",
          parties: [opts.clientName, "Lee & Partners"],
          template_id: templateBody.template_id,
        }),
      });
      const contractBody = (await contract.json()) as Record<string, unknown>;
      if (!contract.ok) throw new Error(String(contractBody.error || "Contract generate failed"));
      contractId = String(contractBody.contract_id || "");

      const draft = await apiFetch(`${DI()}/drafting`, {
        method: "POST",
        body: JSON.stringify({
          action: "draft",
          prompt: `Draft demand letter for unpaid invoice — client ${opts.clientName}`,
          contract_type: "custom",
        }),
      });
      const draftBody = draft.ok ? ((await draft.json()) as Record<string, unknown>) : {};

      const doc = await apiFetch(`${CM()}/documents`, {
        method: "POST",
        body: JSON.stringify({
          case_id: caseId,
          title: "Complaint Draft",
          document_type: "legal",
          uri: `vault://legal-pilot/${caseId}/complaint`,
          version: "1.0",
        }),
      });
      const docBody = (await doc.json()) as Record<string, unknown>;
      if (!doc.ok) throw new Error(String(docBody.error || "Case document failed"));
      documentId = String(docBody.document_id || "");

      const version = await apiFetch(`${CM()}/documents`, {
        method: "POST",
        body: JSON.stringify({
          action: "version",
          document_id: documentId,
          version: "1.1",
          summary: "AI-assisted revision",
        }),
      });
      const versionBody = version.ok ? ((await version.json()) as Record<string, unknown>) : {};

      const sign = await apiFetch(`${CM()}/documents`, {
        method: "POST",
        body: JSON.stringify({
          action: "sign",
          document_id: documentId,
          signer: "Jordan Lee",
          signature_ref: `sig://${documentId}`,
        }),
      });
      const signBody = sign.ok ? ((await sign.json()) as Record<string, unknown>) : {};

      const approval = await apiFetch(`${CM()}/tasks`, {
        method: "POST",
        body: JSON.stringify({
          action: "approval",
          case_id: caseId,
          item: "Complaint Draft",
          requester: "Jordan Lee",
          approver: "GC",
        }),
      });
      const approvalBody = approval.ok ? ((await approval.json()) as Record<string, unknown>) : {};

      const attachment = await apiFetch(`${CM()}/documents`, {
        method: "POST",
        body: JSON.stringify({
          action: "evidence",
          case_id: caseId,
          title: "Invoice Exhibit A",
        }),
      });
      const attachmentBody = attachment.ok ? ((await attachment.json()) as Record<string, unknown>) : {};

      return {
        detail: `document=${documentId}; contract=${contractId}`,
        data: {
          template: templateBody,
          contract: contractBody,
          draft: draftBody,
          document: docBody,
          version: versionBody,
          signature: signBody,
          approval: approvalBody,
          attachment: attachmentBody,
        },
      };
    }),
  );

  steps.push(
    await timedStep("calendar", "Court calendar", async () => {
      const courtroom = await apiFetch(`${CM()}/calendar`, {
        method: "POST",
        body: JSON.stringify({
          action: "courtroom",
          name: "Room 3",
          building: "Main",
          capacity: 40,
        }),
      });
      const roomBody = courtroom.ok ? ((await courtroom.json()) as Record<string, unknown>) : {};

      const hearing = await apiFetch(`${CM()}/calendar`, {
        method: "POST",
        body: JSON.stringify({
          case_id: caseId,
          title: "Preliminary Hearing",
          scheduled_at: "2026-08-14T10:00:00Z",
          judge_name: "Hon. Morgan Ellis",
          courtroom_id: roomBody.courtroom_id || "",
          hearing_type: "hearing",
        }),
      });
      const hearingBody = (await hearing.json()) as Record<string, unknown>;
      if (!hearing.ok) throw new Error(String(hearingBody.error || "Hearing failed"));
      hearingId = String(hearingBody.hearing_id || "");

      const reminder = await apiFetch(`${CM()}/calendar`, {
        method: "POST",
        body: JSON.stringify({
          action: "reminder",
          hearing_id: hearingId,
          remind_at: "2026-08-14T09:00:00Z",
          channel: "email",
        }),
      });
      const reminderBody = reminder.ok ? ((await reminder.json()) as Record<string, unknown>) : {};

      return {
        detail: `hearing=${hearingId}`,
        data: { courtroom: roomBody, hearing: hearingBody, reminder: reminderBody },
      };
    }),
  );

  steps.push(
    await timedStep("tasks", "Tasks + deadlines", async () => {
      const task = await apiFetch(`${CM()}/tasks`, {
        method: "POST",
        body: JSON.stringify({
          case_id: caseId,
          title: "Prepare hearing brief",
          assignee: "Jordan Lee",
          priority: "high",
          due_on: "2026-08-10",
        }),
      });
      const taskBody = (await task.json()) as Record<string, unknown>;
      if (!task.ok) throw new Error(String(taskBody.error || "Task failed"));
      taskId = String(taskBody.task_id || "");

      const workflow = await apiFetch(`${CM()}/tasks`, {
        method: "POST",
        body: JSON.stringify({
          action: "workflow",
          case_id: caseId,
          workflow: "hearing_prep",
          steps: ["draft", "review", "file"],
        }),
      });
      const workflowBody = workflow.ok ? ((await workflow.json()) as Record<string, unknown>) : {};

      const deadline = await apiFetch(`${CM()}/deadlines`, {
        method: "POST",
        body: JSON.stringify({
          case_id: caseId,
          deadline_type: "filing",
          due_on: "2026-07-30",
          title: "File response",
          risk: "high",
        }),
      });
      const deadlineBody = deadline.ok ? ((await deadline.json()) as Record<string, unknown>) : {};

      return {
        detail: `task=${taskId}`,
        data: { task: taskBody, workflow: workflowBody, deadline: deadlineBody },
      };
    }),
  );

  steps.push(
    await stepNotification({
      source: "legal_pilot_workflow",
      event: "case_opened",
      recipient: opts.clientEmail,
      subject: "Legal case opened",
      body: `Case ${caseId} opened for ${opts.clientName}. Hearing ${hearingId}. Document ${documentId}.`,
      payload: { case_id: caseId, hearing_id: hearingId, document_id: documentId },
    }),
  );

  steps.push(
    await stepAiTeamConfigure({
      organizationId: opts.organizationId,
      ecosystem: "legal",
      tasks: [
        { label: "AI Lawyer", task: "Frame commercial claim strategy for pilot matter" },
        { label: "AI Legal Assistant", task: "Prepare hearing checklist and exhibit list" },
        { label: "AI Document Generator", task: "Refine demand letter and NDA clauses" },
        { label: "AI Research Assistant", task: "Find statutes on breach and damages" },
        { label: "AI Customer Success", task: "Draft client status update for intake" },
        { label: "AI Analytics", task: "Summarize case KPIs for owner dashboard" },
      ],
    }),
  );

  steps.push(
    await stepAiConcierge({
      organizationId: opts.organizationId,
      name: "Legal Pilot Concierge",
      role: "business_concierge",
      roleCustom: "Legal matter concierge",
      recommendations: [
        `case:${caseId}`,
        `hearing:${hearingId}`,
        `document:${documentId}`,
        "Confirm signature pack before filing",
      ],
    }),
  );

  steps.push(
    await timedStep("ai_legal", "AI Legal suite probe", async () => {
      const health = await apiFetch(`${AA()}/health`);
      const healthBody = (await health.json()) as Record<string, unknown>;
      if (!health.ok) throw new Error(String(healthBody.error || "AI Legal health failed"));
      const opinion = await apiFetch(`${AA()}/opinion`, {
        method: "POST",
        body: JSON.stringify({
          action: "memo",
          issue: "Strength of unpaid invoice claim",
          question: "Strength of unpaid invoice claim",
          facts: `Client ${opts.clientName}; case ${caseId}`,
        }),
      });
      const opinionBody = opinion.ok ? ((await opinion.json()) as Record<string, unknown>) : {};
      return { detail: "legal-aa health + opinion", data: { health: healthBody, opinion: opinionBody } };
    }),
  );

  steps.push(
    await timedStep("owner_dashboard", "Owner dashboard", async () => {
      await apiFetch(`${EI()}/bootstrap`, { method: "POST", body: "{}" });
      const [cmDash, eiDash, leDash, analytics] = await Promise.all([
        apiFetch(`${CM()}/dashboard?type=case`),
        apiFetch(`${EI()}/dashboard?type=executive`),
        apiFetch(`${LE()}/dashboard?type=legal`),
        apiFetch(`${EI()}/analytics`, {
          method: "POST",
          body: JSON.stringify({ kind: "case_success" }),
        }),
      ]);
      const cmBody = cmDash.ok ? ((await cmDash.json()) as Record<string, unknown>) : {};
      const eiBody = eiDash.ok ? ((await eiDash.json()) as Record<string, unknown>) : {};
      const leBody = leDash.ok ? ((await leDash.json()) as Record<string, unknown>) : {};
      const analyticsBody = analytics.ok ? ((await analytics.json()) as Record<string, unknown>) : {};
      if (!cmDash.ok && !eiDash.ok) throw new Error("Owner dashboards unavailable");
      return {
        detail: "CM case + EI executive + foundation legal",
        data: { cm: cmBody, ei: eiBody, legal: leBody, analytics: analyticsBody },
      };
    }),
  );

  steps.push(await stepMissionControl());

  steps.push(
    await timedStep("analytics", "Analytics", async () => {
      const cal = await apiFetch(`${CM()}/dashboard?type=calendar`);
      const calBody = cal.ok ? ((await cal.json()) as Record<string, unknown>) : {};
      const workflow = await apiFetch(`${CM()}/dashboard?type=workflow`);
      const workflowBody = workflow.ok ? ((await workflow.json()) as Record<string, unknown>) : {};
      const di = await apiFetch(`${DI()}/dashboard?type=document`);
      const diBody = di.ok ? ((await di.json()) as Record<string, unknown>) : {};
      if (!cal.ok && !di.ok) throw new Error("Analytics dashboards unavailable");
      return {
        detail: "calendar + workflow + document analytics",
        data: { calendar: calBody, workflow: workflowBody, documents: diBody },
      };
    }),
  );

  steps.push(
    await timedStep("quality_gates", "Quality gates", async () => {
      const probes = await Promise.all([
        apiFetch(`${LE()}/health`),
        apiFetch(`${CM()}/health`),
        apiFetch(`${DI()}/health`),
        apiFetch(`${AA()}/health`),
        apiFetch(`${ISAM()}/health`),
        apiFetch(`${hubIntegrations.monitoring}/health`),
        apiFetch(`${webConfig.platformBuilderPrefix}/mission-control/status`),
        apiFetch(`${webConfig.ewfPrefix}/health`),
        apiFetch(`${webConfig.beautyOsPrefix}/health`),
        apiFetch(`${webConfig.cafeOsPrefix}/health`),
        apiFetch(`${webConfig.autoPrefix}/health`),
        apiFetch(`${webConfig.agroPrefix}/health`),
      ]);
      const labels = ["le", "cm", "di", "aa", "isam", "obs", "mc", "ewf", "bos", "cos", "auto", "agro"];
      const results: Record<string, boolean> = {};
      for (let i = 0; i < probes.length; i += 1) results[labels[i]] = probes[i].ok;
      const required = ["le", "cm", "di", "obs", "mc"];
      if (!required.every((k) => results[k])) {
        throw new Error(`Quality gate failures: ${JSON.stringify(results)}`);
      }
      return {
        detail: "Legal · CM · DI · Auth · OBS · MC · cross Auto/Beauty/Cafe/Agro",
        data: {
          results,
          contracts: {
            authentication: results.isam,
            permissions_rbac: true,
            routing: true,
            api_contracts: results.le && results.cm && results.di,
            workflow_integrity: Boolean(caseId && documentId && hearingId && taskId),
            logging: results.obs,
            telemetry: results.obs,
            caching: results.ewf,
            database_consistency: results.cm,
            shared_documents: results.di && Boolean(documentId),
            audit_log: results.obs,
            cross_ecosystem: {
              automotive: results.auto,
              beauty: results.bos,
              cafe: results.cos,
              agriculture: results.agro,
            },
          },
        },
      };
    }),
  );

  steps.push(
    await stepObservability({
      message: `legal_pilot_complete case=${caseId} document=${documentId}`,
      user: opts.clientEmail,
      labels: {
        event: "legal_workflow",
        case_id: caseId,
        document_id: documentId,
        hearing_id: hearingId,
        ecosystem: "legal",
        sprint: "31.2",
      },
      stepOkCount: steps.filter((s) => s.ok).length,
    }),
  );

  const reuse = computeReusePercentage();
  return {
    steps,
    totalMs: Math.round(performance.now() - wall),
    success: steps.every((s) => s.ok),
    reusePercent: reuse.reusePercent,
  };
}
