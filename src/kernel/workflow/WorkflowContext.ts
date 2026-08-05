import type { IWorkflowContext } from "./interfaces.js";

/**
 * Mutable per-instance context bag shared across steps.
 */
export class WorkflowContext implements IWorkflowContext {
  readonly instanceId: string;
  readonly definitionId: string;
  private readonly data: Record<string, unknown>;

  constructor(
    instanceId: string,
    definitionId: string,
    initial?: Readonly<Record<string, unknown>>,
  ) {
    this.instanceId = instanceId;
    this.definitionId = definitionId;
    this.data = { ...(initial ?? {}) };
  }

  get<T = unknown>(key: string): T | undefined {
    return this.data[key] as T | undefined;
  }

  set(key: string, value: unknown): void {
    this.data[key] = value;
  }

  entries(): Readonly<Record<string, unknown>> {
    return Object.freeze({ ...this.data });
  }

  snapshot(): Record<string, unknown> {
    return { ...this.data };
  }
}
