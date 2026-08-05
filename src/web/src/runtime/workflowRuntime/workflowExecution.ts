/**
 * Workflow execution engine — Sprint 28.8.
 * Node runners reuse Command Runtime + Event Bus + Notification Store.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { useNotificationStore } from "@/notifications/notificationStore";
import { workflowRegistry } from "./workflowRegistry";
import { logSession, workflowSessions } from "./workflowSession";
import type {
  NodeExecutionRecord,
  WorkflowDefinition,
  WorkflowNodeDef,
  WorkflowSession,
} from "./workflowTypes";

type TickOptions = { signalEvent?: { type: string; payload?: Record<string, unknown> } };

function ensureRecord(session: WorkflowSession, node: WorkflowNodeDef): NodeExecutionRecord {
  if (!session.nodeRecords[node.id]) {
    session.nodeRecords[node.id] = {
      nodeId: node.id,
      kind: node.kind,
      label: node.label,
      status: "pending",
      retryCount: 0,
    };
  }
  return session.nodeRecords[node.id]!;
}

function finishNode(
  session: WorkflowSession,
  rec: NodeExecutionRecord,
  status: NodeExecutionRecord["status"],
  output?: unknown,
  error?: string,
) {
  rec.status = status;
  rec.finishedAt = new Date().toISOString();
  if (rec.startedAt) {
    rec.durationMs = Math.max(0, Date.now() - new Date(rec.startedAt).getTime());
  }
  if (output !== undefined) rec.output = output;
  if (error) rec.error = error;
  session.context.outputs[rec.nodeId] = output ?? null;
  session.updatedAt = new Date().toISOString();
  session.snapshotVersion += 1;
}

async function runNode(
  session: WorkflowSession,
  def: WorkflowDefinition,
  node: WorkflowNodeDef,
  opts: TickOptions,
): Promise<string[]> {
  const rec = ensureRecord(session, node);
  rec.status = "running";
  rec.startedAt = new Date().toISOString();
  logSession(session, "info", `Running ${node.kind}: ${node.label}`, node.id);

  try {
    switch (node.kind) {
      case "start":
      case "sequential":
      case "end": {
        finishNode(session, rec, "done", { ok: true });
        return node.next || [];
      }

      case "parallel": {
        const branches = node.branches || [];
        const next: string[] = [];
        for (const branch of branches) {
          if (branch[0]) next.push(branch[0]);
        }
        // Also continue sequential next after all branch heads scheduled
        finishNode(session, rec, "done", { branches: branches.length });
        return next.length ? next : node.next || [];
      }

      case "condition": {
        const key = node.conditionKey || "condition";
        const truthy = Boolean(session.context.vars[key]);
        finishNode(session, rec, "done", { result: truthy });
        return truthy ? node.whenTrue || node.next || [] : node.whenFalse || node.next || [];
      }

      case "loop": {
        const iterKey = `__loop_${node.id}`;
        const iter = Number(session.context.temp[iterKey] || 0);
        const max = node.maxIterations ?? 3;
        if (iter < max) {
          session.context.temp[iterKey] = iter + 1;
          finishNode(session, rec, "done", { iteration: iter + 1 });
          return node.body?.length ? node.body : node.next || [];
        }
        finishNode(session, rec, "done", { iteration: iter, done: true });
        return node.next || [];
      }

      case "delay": {
        const ms = node.delayMs ?? 0;
        if (ms <= 0) {
          finishNode(session, rec, "done", { delayed: 0 });
          return node.next || [];
        }
        session.status = "waiting";
        session.waitUntil = new Date(Date.now() + ms).toISOString();
        session.cursor = [node.id];
        rec.status = "waiting";
        logSession(session, "info", `Delay ${ms}ms`, node.id);
        workflowSessions.set(session);
        setTimeout(() => {
          const live = workflowSessions.get(session.id);
          if (!live || live.status === "cancelled") return;
          if (live.status !== "waiting" && live.status !== "paused") return;
          finishNode(live, ensureRecord(live, node), "done", { delayed: ms });
          live.status = "running";
          live.waitUntil = undefined;
          live.cursor = node.next || [];
          workflowSessions.set(live);
          void advanceSession(live.id);
        }, Math.min(ms, 60_000));
        return [];
      }

      case "wait_event": {
        if (opts.signalEvent && opts.signalEvent.type === (node.eventType || "workflow_update")) {
          finishNode(session, rec, "done", opts.signalEvent.payload);
          return node.next || [];
        }
        session.status = "waiting";
        session.waitEventType = node.eventType || "workflow_update";
        session.cursor = [node.id];
        rec.status = "waiting";
        logSession(session, "info", `Waiting for event ${session.waitEventType}`, node.id);
        return [];
      }

      case "approval": {
        if (session.context.vars.approved === true) {
          finishNode(session, rec, "done", { approved: true });
          session.approvalPending = false;
          return node.next || [];
        }
        if (session.context.vars.approved === false) {
          finishNode(session, rec, "failed", { approved: false }, "approval_rejected");
          session.status = "failed";
          return [];
        }
        session.status = "paused";
        session.approvalPending = true;
        session.cursor = [node.id];
        rec.status = "waiting";
        logSession(session, "warn", "Awaiting approval", node.id);
        return [];
      }

      case "notification": {
        useNotificationStore.getState().push({
          kind: "workflow",
          title: node.notificationTitle || node.label,
          body: node.notificationBody || `Workflow ${def.name}`,
          level: "info",
        });
        finishNode(session, rec, "done", { notified: true });
        return node.next || [];
      }

      case "command": {
        const cmdId = node.commandId || "open_dashboard";
        const result = await commandRuntime.execute(cmdId, {
          ...(node.commandArgs || {}),
          via: "workflow",
          workflowSessionId: session.id,
        });
        if (!result.ok) {
          rec.retryCount += 1;
          finishNode(session, rec, "failed", result, result.error);
          session.status = "failed";
          return [];
        }
        finishNode(session, rec, "done", result);
        return node.next || [];
      }

      case "ai_action": {
        const utterance = node.utterance || String(session.context.vars.utterance || node.label);
        // AI → Command Runtime only
        const result = node.commandId
          ? await commandRuntime.execute(node.commandId, {
              ...(node.commandArgs || {}),
              via: "ai",
              workflowSessionId: session.id,
            })
          : await commandRuntime.routeAiIntent(utterance);
        if (!result.ok) {
          rec.retryCount += 1;
          finishNode(session, rec, "failed", result, result.error);
          session.status = "failed";
          return [];
        }
        finishNode(session, rec, "done", result);
        return node.next || [];
      }

      case "http":
      case "webhook": {
        const url = node.url || "https://example.invalid/workflow-hook";
        const method = (node.method || "POST").toUpperCase();
        // Demo-safe: simulate HTTP without external dependency when offline
        try {
          if (typeof fetch === "function" && url.includes("example.invalid")) {
            finishNode(session, rec, "done", { simulated: true, url, method, status: 200 });
          } else if (typeof fetch === "function") {
            const res = await fetch(url, {
              method,
              headers: { "Content-Type": "application/json" },
              body: method === "GET" ? undefined : JSON.stringify(session.context.vars),
            });
            finishNode(session, rec, "done", { status: res.status, ok: res.ok });
            if (!res.ok) {
              session.status = "failed";
              return [];
            }
          } else {
            finishNode(session, rec, "done", { simulated: true, url, method });
          }
        } catch (e) {
          finishNode(
            session,
            rec,
            "failed",
            null,
            e instanceof Error ? e.message : "http_failed",
          );
          session.status = "failed";
          return [];
        }
        return node.next || [];
      }

      case "script": {
        // Future-ready stub
        finishNode(session, rec, "done", {
          scriptId: node.scriptId || "noop",
          futureReady: true,
        });
        return node.next || [];
      }

      default: {
        finishNode(session, rec, "done", { skipped: true });
        return node.next || [];
      }
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : "node_error";
    finishNode(session, rec, "failed", null, msg);
    session.status = "failed";
    logSession(session, "error", msg, node.id);
    return [];
  }
}

export async function advanceSession(sessionId: string, opts: TickOptions = {}) {
  const session = workflowSessions.get(sessionId);
  if (!session) return null;
  if (session.status === "paused" || session.status === "cancelled") return session;
  if (session.status === "completed" || session.status === "failed") return session;

  const def = workflowRegistry.get(session.definitionId);
  if (!def) {
    session.status = "failed";
    logSession(session, "error", "definition_missing");
    workflowSessions.set(session);
    return session;
  }

  session.status = "running";
  let guard = 0;
  while (session.cursor.length && guard++ < 50) {
    if (session.status !== "running") break;
    const nodeId = session.cursor.shift()!;
    const node = def.nodes[nodeId];
    if (!node) {
      logSession(session, "warn", `Missing node ${nodeId}`);
      continue;
    }
    const nextIds = await runNode(session, def, node, opts);
    const statusAfter = session.status as WorkflowSession["status"];
    if (statusAfter === "waiting" || statusAfter === "paused" || statusAfter === "failed") {
      workflowSessions.set(session);
      publishWorkflowUpdate(session);
      return session;
    }
    for (const n of nextIds) {
      if (!session.cursor.includes(n)) session.cursor.push(n);
    }
    if (node.kind === "end" || (node.kind === "start" && !nextIds.length && !node.next?.length)) {
      // continue
    }
  }

  if (session.status === "running" && session.cursor.length === 0) {
    const failed = Object.values(session.nodeRecords).some((r) => r.status === "failed");
    session.status = failed ? "failed" : "completed";
    session.completedAt = new Date().toISOString();
    logSession(session, failed ? "error" : "info", failed ? "Workflow failed" : "Workflow completed");
  }

  workflowSessions.set(session);
  publishWorkflowUpdate(session);
  return session;
}

function publishWorkflowUpdate(session: WorkflowSession) {
  enterpriseEventBus.publish({
    type: "workflow_update",
    source: "system",
    payload: {
      sessionId: session.id,
      definitionId: session.definitionId,
      status: session.status,
      cursor: session.cursor,
      approvalPending: session.approvalPending,
    },
  });
}

export function attachWorkflowEventBridge() {
  return enterpriseEventBus.subscribe((event) => {
    for (const session of workflowSessions.list()) {
      if (session.status !== "waiting" || !session.waitEventType) continue;
      if (event.type !== session.waitEventType) continue;
      const def = workflowRegistry.get(session.definitionId);
      const waitingNodeId = Object.values(session.nodeRecords).find((r) => r.status === "waiting")?.nodeId;
      const node = waitingNodeId ? def?.nodes[waitingNodeId] : undefined;
      session.status = "running";
      session.waitEventType = undefined;
      if (node) {
        void advanceSession(session.id, {
          signalEvent: { type: event.type, payload: event.payload },
        });
      } else {
        workflowSessions.set(session);
        void advanceSession(session.id, {
          signalEvent: { type: event.type, payload: event.payload },
        });
      }
    }
  });
}
