/**
 * Seed workflow definitions — Sprint 28.8.
 * Projects BUSINESS_WORKFLOW_TEMPLATES + engine demos into WorkflowDefinition graphs.
 */

import { BUSINESS_WORKFLOW_TEMPLATES } from "@/enterprise-workflow/workflowTemplates";
import type { WorkflowDefinition, WorkflowNodeDef } from "./workflowTypes";

function chainFromTemplate(templateId: string): WorkflowDefinition | null {
  const t = BUSINESS_WORKFLOW_TEMPLATES.find((x) => x.id === templateId);
  if (!t) return null;
  const nodes: Record<string, WorkflowNodeDef> = {};
  t.steps.forEach((step, i) => {
    const next = t.steps[i + 1];
    let kind: WorkflowNodeDef["kind"] = "sequential";
    if (step.kind === "start") kind = "start";
    else if (step.kind === "finish") kind = "end";
    else if (step.kind === "ai") kind = "ai_action";
    else if (step.kind === "notification") kind = "notification";
    else if (step.kind === "module" || step.kind === "knowledge") kind = "command";

    nodes[step.id] = {
      id: step.id,
      kind,
      label: step.label,
      next: next ? [next.id] : undefined,
      utterance: step.kind === "ai" ? `open ${step.agent || "dashboard"}` : undefined,
      commandId:
        step.kind === "module" || step.kind === "knowledge"
          ? "act_open_knowledge"
          : step.kind === "ai"
            ? undefined
            : undefined,
      notificationTitle: step.kind === "notification" ? step.label : undefined,
      notificationBody: step.kind === "notification" ? t.description : undefined,
    };
  });

  // Prefer CRM open for first AI after start when template is CRM-ish
  const firstAi = t.steps.find((s) => s.kind === "ai");
  if (firstAi && nodes[firstAi.id]) {
    nodes[firstAi.id]!.commandId = "open_crm";
    nodes[firstAi.id]!.utterance = undefined;
  }

  return {
    id: `tpl_${t.id}`,
    name: t.title,
    description: t.description,
    version: "1.0",
    entryNodeId: t.steps[0]!.id,
    nodes,
    tags: ["template", t.hubKind],
    source: "template",
  };
}

export function buildSeedWorkflows(): WorkflowDefinition[] {
  const fromTemplates = BUSINESS_WORKFLOW_TEMPLATES.map((t) => chainFromTemplate(t.id)!).filter(Boolean);

  const demoParallel: WorkflowDefinition = {
    id: "demo_parallel_ops",
    name: "Parallel Ops Pulse",
    description: "Start → Parallel (CRM + City) → Notification → End",
    version: "1.0",
    entryNodeId: "n0",
    source: "catalog",
    tags: ["demo", "parallel"],
    nodes: {
      n0: { id: "n0", kind: "start", label: "Start", next: ["n1"] },
      n1: {
        id: "n1",
        kind: "parallel",
        label: "Open CRM + City",
        branches: [["n2"], ["n3"]],
        next: ["n4"],
      },
      n2: { id: "n2", kind: "command", label: "Open CRM", commandId: "open_crm", next: ["n4"] },
      n3: {
        id: "n3",
        kind: "command",
        label: "Open City",
        commandId: "open_enterprise_city",
        next: ["n4"],
      },
      n4: {
        id: "n4",
        kind: "notification",
        label: "Notify",
        notificationTitle: "Parallel pulse complete",
        notificationBody: "CRM and City commands dispatched",
        next: ["n5"],
      },
      n5: { id: "n5", kind: "end", label: "End" },
    },
  };

  const demoApproval: WorkflowDefinition = {
    id: "demo_approval_gate",
    name: "Approval Gate",
    description: "Start → Approval → Command → End (pause until approved)",
    version: "1.0",
    entryNodeId: "a0",
    source: "catalog",
    tags: ["demo", "approval"],
    nodes: {
      a0: { id: "a0", kind: "start", label: "Start", next: ["a1"] },
      a1: { id: "a1", kind: "approval", label: "Manager Approval", next: ["a2"] },
      a2: {
        id: "a2",
        kind: "command",
        label: "Open Production",
        commandId: "qa_production",
        next: ["a3"],
      },
      a3: { id: "a3", kind: "end", label: "End" },
    },
  };

  const demoWait: WorkflowDefinition = {
    id: "demo_wait_event",
    name: "Wait Runtime Event",
    description: "Start → Wait workflow_update → Notification → End",
    version: "1.0",
    entryNodeId: "w0",
    source: "catalog",
    tags: ["demo", "event"],
    nodes: {
      w0: { id: "w0", kind: "start", label: "Start", next: ["w1"] },
      w1: {
        id: "w1",
        kind: "wait_event",
        label: "Wait workflow_update",
        eventType: "runtime_update",
        next: ["w2"],
      },
      w2: {
        id: "w2",
        kind: "notification",
        label: "Event received",
        notificationTitle: "Workflow resumed",
        notificationBody: "runtime_update observed",
        next: ["w3"],
      },
      w3: { id: "w3", kind: "end", label: "End" },
    },
  };

  return [...fromTemplates, demoParallel, demoApproval, demoWait];
}
