import type { WorkflowInstanceStatus } from "./types.js";

const ALLOWED: Readonly<
  Record<WorkflowInstanceStatus, readonly WorkflowInstanceStatus[]>
> = {
  Created: ["Running", "Cancelled"],
  Running: [
    "WaitingApproval",
    "WaitingEvent",
    "Suspended",
    "Completed",
    "Failed",
    "Compensating",
    "Cancelled",
  ],
  WaitingApproval: ["Running", "Failed", "Cancelled", "Suspended"],
  WaitingEvent: ["Running", "Failed", "Cancelled", "Suspended"],
  Suspended: ["Running", "Cancelled", "Failed"],
  Completed: [],
  Failed: ["Compensating"],
  Compensating: ["Compensated", "Failed", "Cancelled"],
  Compensated: [],
  Cancelled: [],
};

/**
 * Workflow instance lifecycle transitions.
 */
export class WorkflowState {
  private _status: WorkflowInstanceStatus;

  constructor(initial: WorkflowInstanceStatus = "Created") {
    this._status = initial;
  }

  get status(): WorkflowInstanceStatus {
    return this._status;
  }

  canTransition(to: WorkflowInstanceStatus): boolean {
    if (to === this._status) return true;
    return ALLOWED[this._status].includes(to);
  }

  transition(to: WorkflowInstanceStatus): void {
    if (to === this._status) return;
    if (!this.canTransition(to)) {
      throw new Error(
        `Invalid workflow state transition: ${this._status} → ${to}`,
      );
    }
    this._status = to;
  }

  assert(...allowed: WorkflowInstanceStatus[]): void {
    if (!allowed.includes(this._status)) {
      throw new Error(
        `Expected workflow status in [${allowed.join(", ")}], got ${this._status}`,
      );
    }
  }
}
