import type { IWorkflow } from "./interfaces.js";
import type { WorkflowDefinitionInit } from "./types.js";
import { WorkflowStep } from "./WorkflowStep.js";

/**
 * Immutable workflow graph definition.
 */
export class WorkflowDefinition implements IWorkflow {
  readonly id: string;
  readonly name: string;
  readonly version: string;
  readonly start: string;
  readonly metadata: Readonly<Record<string, unknown>>;
  private readonly steps: ReadonlyMap<string, WorkflowStep>;

  private constructor(
    init: WorkflowDefinitionInit,
    steps: ReadonlyMap<string, WorkflowStep>,
  ) {
    this.id = init.id;
    this.name = init.name ?? init.id;
    this.version = init.version;
    this.start = init.start;
    this.metadata = Object.freeze({ ...(init.metadata ?? {}) });
    this.steps = steps;
  }

  static create(init: WorkflowDefinitionInit): WorkflowDefinition {
    if (!init.id || !init.version || !init.start) {
      throw new Error("WorkflowDefinition requires id, version, and start");
    }
    const map = new Map<string, WorkflowStep>();
    for (const s of init.steps) {
      if (map.has(s.id)) {
        throw new Error(`Duplicate workflow step id: ${s.id}`);
      }
      map.set(s.id, new WorkflowStep(s));
    }
    return new WorkflowDefinition(init, map);
  }

  getStep(id: string): WorkflowStep | undefined {
    return this.steps.get(id);
  }

  listSteps(): readonly WorkflowStep[] {
    return Object.freeze([...this.steps.values()]);
  }
}
