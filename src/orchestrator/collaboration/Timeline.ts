import type { TimelineEvent } from "./types.js";

export type CollaborationEventType =
  | "workflow.started"
  | "workflow.finished"
  | "workflow.failed"
  | "workflow.paused"
  | "workflow.resumed"
  | "workflow.step.started"
  | "workflow.step.finished"
  | "agent.online"
  | "agent.offline"
  | "agent.busy"
  | "agent.idle"
  | "agent.failed"
  | "provider.connected"
  | "provider.disconnected";

/**
 * Durable execution timeline for collaboration workflows.
 */
export class CollaborationTimeline {
  private readonly events: TimelineEvent[] = [];
  private readonly max: number;

  constructor(max = 5_000) {
    this.max = max;
  }

  push(
    event: Omit<TimelineEvent, "id" | "at"> & { id?: string; at?: string },
  ): TimelineEvent {
    const full: TimelineEvent = {
      id:
        event.id ??
        `tl_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
      at: event.at ?? new Date().toISOString(),
      type: event.type,
      ...(event.workflowId !== undefined ? { workflowId: event.workflowId } : {}),
      ...(event.agentId !== undefined ? { agentId: event.agentId } : {}),
      ...(event.providerId !== undefined ? { providerId: event.providerId } : {}),
      ...(event.stepId !== undefined ? { stepId: event.stepId } : {}),
      ...(event.durationMs !== undefined ? { durationMs: event.durationMs } : {}),
      ...(event.result !== undefined ? { result: event.result } : {}),
      ...(event.error !== undefined ? { error: event.error } : {}),
      ...(event.artifacts !== undefined ? { artifacts: event.artifacts } : {}),
      ...(event.message !== undefined ? { message: event.message } : {}),
    };
    this.events.push(full);
    if (this.events.length > this.max) this.events.shift();
    return full;
  }

  list(opts?: {
    workflowId?: string;
    agentId?: string;
    limit?: number;
  }): TimelineEvent[] {
    let rows = [...this.events].reverse();
    if (opts?.workflowId) {
      rows = rows.filter((e) => e.workflowId === opts.workflowId);
    }
    if (opts?.agentId) {
      rows = rows.filter((e) => e.agentId === opts.agentId);
    }
    return rows.slice(0, opts?.limit ?? 200);
  }

  clear(): void {
    this.events.length = 0;
  }
}
