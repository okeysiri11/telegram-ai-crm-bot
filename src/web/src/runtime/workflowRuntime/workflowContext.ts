/**
 * Workflow session factory + context helpers — Sprint 28.8.
 */

import type { WorkflowContext, WorkflowDefinition, WorkflowSession } from "./workflowTypes";

export function createWorkflowContext(
  def: WorkflowDefinition,
  sessionId: string,
  initialVars: Record<string, unknown> = {},
): WorkflowContext {
  return {
    vars: { ...initialVars },
    memory: {},
    outputs: {},
    temp: {},
    meta: {
      workflowId: sessionId,
      definitionId: def.id,
      startedAt: new Date().toISOString(),
      surface: String(initialVars.surface || "system"),
      tenantId: (initialVars.tenantId as string) || null,
    },
  };
}

export function createWorkflowSession(
  def: WorkflowDefinition,
  initialVars: Record<string, unknown> = {},
): WorkflowSession {
  const id = `wfs_${Math.random().toString(36).slice(2, 10)}`;
  const now = new Date().toISOString();
  return {
    id,
    definitionId: def.id,
    status: "running",
    context: createWorkflowContext(def, id, initialVars),
    nodeRecords: {},
    cursor: [def.entryNodeId],
    logs: [
      {
        id: `log_${Math.random().toString(36).slice(2, 8)}`,
        at: now,
        level: "info",
        message: `Started workflow ${def.name}`,
      },
    ],
    startedAt: now,
    updatedAt: now,
    retryCount: 0,
    snapshotVersion: 1,
  };
}

export function logSession(
  session: WorkflowSession,
  level: "info" | "warn" | "error" | "debug",
  message: string,
  nodeId?: string,
) {
  session.logs.unshift({
    id: `log_${Math.random().toString(36).slice(2, 8)}`,
    at: new Date().toISOString(),
    level,
    message,
    nodeId,
  });
  if (session.logs.length > 200) session.logs.length = 200;
  session.updatedAt = new Date().toISOString();
}
