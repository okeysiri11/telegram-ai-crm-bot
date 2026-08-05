/**
 * Sprint 31.2 — Client-side n8n bridge helpers + workflow library.
 * Execution history is advisory; Platform Runtime remains SoR.
 */

export type WorkflowTemplate = {
  id: string;
  name: string;
  version: string;
  description: string;
  trigger: "webhook" | "schedule" | "manual";
  tags: string[];
  /** Platform APIs that own state after callback */
  platformTargets: string[];
};

export type WorkflowExecutionRecord = {
  id: string;
  workflowId: string;
  templateId: string | null;
  status: "pending" | "running" | "success" | "failed" | "cancelled";
  startedAt: string;
  finishedAt?: string;
  source: "n8n" | "platform";
};

const SESSION_KEY = "ews_n8n_exec_v1";

export const WORKFLOW_LIBRARY: WorkflowTemplate[] = [
  {
    id: "n8n_tpl_lead_notify",
    name: "Lead → Notify",
    version: "1.0.0",
    description: "Webhook lead intake; CRM + notifications own state.",
    trigger: "webhook",
    tags: ["crm", "comms"],
    platformTargets: ["/crm", "/notifications"],
  },
  {
    id: "n8n_tpl_media_pipeline",
    name: "Media Pipeline Fan-out",
    version: "1.0.0",
    description: "Starts Production Runtime jobs; n8n does not render.",
    trigger: "manual",
    tags: ["production", "media"],
    platformTargets: ["/production-studio", "/platform-builder/runtime"],
  },
  {
    id: "n8n_tpl_provider_health",
    name: "Provider Health Sweep",
    version: "1.0.0",
    description: "Calls APH health; Runtime records results.",
    trigger: "schedule",
    tags: ["aph", "ops"],
    platformTargets: ["/health", "/integrations"],
  },
  {
    id: "n8n_tpl_prompt_batch",
    name: "Prompt Batch",
    version: "1.0.0",
    description: "Batch prompt runs via APH with firewall + cost track.",
    trigger: "manual",
    tags: ["ai", "studio"],
    platformTargets: ["/ai-studio", "/production-studio"],
  },
];

function readExecutions(): WorkflowExecutionRecord[] {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as WorkflowExecutionRecord[];
  } catch {
    return [];
  }
}

function writeExecutions(items: WorkflowExecutionRecord[]) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(items.slice(0, 40)));
  } catch {
    /* ignore */
  }
}

export function listWorkflowTemplates(): WorkflowTemplate[] {
  return WORKFLOW_LIBRARY.slice();
}

export function getWorkflowTemplate(id: string): WorkflowTemplate | undefined {
  return WORKFLOW_LIBRARY.find((t) => t.id === id);
}

/** Launch n8n-orchestrated workflow — records intent; Runtime owns side effects. */
export function launchN8nWorkflow(templateId: string, workflowId?: string): WorkflowExecutionRecord {
  const tpl = getWorkflowTemplate(templateId);
  const record: WorkflowExecutionRecord = {
    id: `n8n_ex_${Date.now().toString(36)}`,
    workflowId: workflowId || `wf_${templateId}`,
    templateId: tpl?.id || templateId,
    status: "running",
    startedAt: new Date().toISOString(),
    source: "n8n",
  };
  const next = [record, ...readExecutions()];
  writeExecutions(next);
  return record;
}

export function completeN8nExecution(
  executionId: string,
  status: "success" | "failed" | "cancelled" = "success",
): WorkflowExecutionRecord | null {
  const items = readExecutions();
  const idx = items.findIndex((e) => e.id === executionId);
  if (idx < 0) return null;
  items[idx] = {
    ...items[idx],
    status,
    finishedAt: new Date().toISOString(),
  };
  writeExecutions(items);
  return items[idx];
}

export function listN8nExecutions(): WorkflowExecutionRecord[] {
  return readExecutions();
}

export function n8nMonitorSnapshot() {
  const items = readExecutions();
  const byStatus: Record<string, number> = {};
  for (const e of items) byStatus[e.status] = (byStatus[e.status] || 0) + 1;
  return {
    templates: WORKFLOW_LIBRARY.length,
    executions: items.length,
    byStatus,
    systemOfRecord: "platform_runtime",
    externalOrchestrator: "n8n",
    businessLogicInN8n: false,
  };
}

export const N8N_UI = {
  defaultUrl: import.meta.env.VITE_N8N_URL || "http://localhost:5678",
  callbackPath: "/integrations/n8n/callback",
  composeFile: "docker-compose.n8n.yml",
} as const;
