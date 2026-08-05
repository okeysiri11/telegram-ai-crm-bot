import type { WorkflowDefinition } from "./WorkflowDefinition.js";

export interface ValidationIssue {
  readonly level: "error" | "warning";
  readonly message: string;
  readonly stepId?: string;
}

/**
 * Validates workflow graphs before registration/start.
 */
export class WorkflowValidator {
  validate(definition: WorkflowDefinition): readonly ValidationIssue[] {
    const issues: ValidationIssue[] = [];
    const steps = definition.listSteps();
    const ids = new Set(steps.map((s) => s.id));

    if (!ids.has(definition.start)) {
      issues.push({
        level: "error",
        message: `Start step "${definition.start}" does not exist`,
      });
    }

    for (const step of steps) {
      for (const n of step.next) {
        if (!ids.has(n)) {
          issues.push({
            level: "error",
            stepId: step.id,
            message: `Next step "${n}" missing`,
          });
        }
      }
      if (step.kind === "parallel" && step.next.length < 2) {
        issues.push({
          level: "warning",
          stepId: step.id,
          message: "Parallel step should have at least 2 branches",
        });
      }
      if (step.kind === "condition") {
        if (!step.condition) {
          issues.push({
            level: "error",
            stepId: step.id,
            message: "Condition step requires condition fn",
          });
        }
        if (!step.whenTrue && !step.whenFalse) {
          issues.push({
            level: "error",
            stepId: step.id,
            message: "Condition step requires whenTrue and/or whenFalse",
          });
        }
      }
      if (step.kind === "task" && !step.handlerId && !step.capability) {
        issues.push({
          level: "warning",
          stepId: step.id,
          message: "Task step has neither handlerId nor capability",
        });
      }
      if (step.compensateWith && !ids.has(step.compensateWith)) {
        issues.push({
          level: "error",
          stepId: step.id,
          message: `Compensation step "${step.compensateWith}" missing`,
        });
      }
      if (step.onError && !ids.has(step.onError)) {
        issues.push({
          level: "error",
          stepId: step.id,
          message: `onError step "${step.onError}" missing`,
        });
      }
      if (step.whenTrue && !ids.has(step.whenTrue)) {
        issues.push({
          level: "error",
          stepId: step.id,
          message: `whenTrue "${step.whenTrue}" missing`,
        });
      }
      if (step.whenFalse && !ids.has(step.whenFalse)) {
        issues.push({
          level: "error",
          stepId: step.id,
          message: `whenFalse "${step.whenFalse}" missing`,
        });
      }
    }

    // Reachability from start (BFS)
    const reachable = new Set<string>();
    const queue = [definition.start];
    while (queue.length > 0) {
      const id = queue.shift()!;
      if (reachable.has(id)) continue;
      reachable.add(id);
      const step = definition.getStep(id);
      if (!step) continue;
      for (const n of step.next) queue.push(n);
      if (step.whenTrue) queue.push(step.whenTrue);
      if (step.whenFalse) queue.push(step.whenFalse);
      if (step.onError) queue.push(step.onError);
      if (step.compensateWith) queue.push(step.compensateWith);
    }
    for (const step of steps) {
      if (!reachable.has(step.id) && step.kind !== "compensation") {
        issues.push({
          level: "warning",
          stepId: step.id,
          message: "Step may be unreachable from start",
        });
      }
    }

    return Object.freeze(issues);
  }

  assertValid(definition: WorkflowDefinition): void {
    const errors = this.validate(definition).filter((i) => i.level === "error");
    if (errors.length > 0) {
      throw new Error(
        `Invalid workflow "${definition.id}": ${errors.map((e) => e.message).join("; ")}`,
      );
    }
  }
}
