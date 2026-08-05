import type { IWorkflowStep } from "./interfaces.js";
import type {
  ConditionFn,
  RetryPolicy,
  StepTimeout,
  WorkflowStepInit,
  WorkflowStepKind,
} from "./types.js";

/**
 * Single node in a workflow definition graph.
 */
export class WorkflowStep implements IWorkflowStep {
  readonly id: string;
  readonly name: string;
  readonly kind: WorkflowStepKind;
  readonly next: readonly string[];
  readonly onError?: string;
  readonly compensateWith?: string;
  readonly retry?: RetryPolicy;
  readonly timeout?: StepTimeout;
  readonly condition?: ConditionFn;
  readonly whenTrue?: string;
  readonly whenFalse?: string;
  readonly capability?: string;
  readonly handlerId?: string;
  readonly method: string;
  readonly join: "all" | "any";
  readonly waitEventType?: string;
  readonly approvalRole?: string;
  readonly metadata: Readonly<Record<string, unknown>>;

  constructor(init: WorkflowStepInit) {
    this.id = init.id;
    this.name = init.name ?? init.id;
    this.kind = init.kind;
    this.next = Object.freeze([...(init.next ?? [])]);
    this.method = init.method ?? "execute";
    this.join = init.join ?? "all";
    this.metadata = Object.freeze({ ...(init.metadata ?? {}) });
    if (init.onError !== undefined) this.onError = init.onError;
    if (init.compensateWith !== undefined)
      this.compensateWith = init.compensateWith;
    if (init.retry !== undefined) this.retry = init.retry;
    if (init.timeout !== undefined) this.timeout = init.timeout;
    if (init.condition !== undefined) this.condition = init.condition;
    if (init.whenTrue !== undefined) this.whenTrue = init.whenTrue;
    if (init.whenFalse !== undefined) this.whenFalse = init.whenFalse;
    if (init.capability !== undefined) this.capability = init.capability;
    if (init.handlerId !== undefined) this.handlerId = init.handlerId;
    if (init.waitEventType !== undefined)
      this.waitEventType = init.waitEventType;
    if (init.approvalRole !== undefined) this.approvalRole = init.approvalRole;
  }
}
