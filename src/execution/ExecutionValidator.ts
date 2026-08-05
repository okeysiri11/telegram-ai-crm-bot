import type { ExecutionTask } from "./types.js";

export interface TaskValidationResult {
  readonly ok: boolean;
  readonly errors: readonly string[];
  readonly checks: Readonly<Record<string, boolean>>;
}

/**
 * Verifies task completion signals from Orchestrator results.
 */
export class ExecutionValidator {
  validateTask(
    task: ExecutionTask,
    agentResult: { ok: boolean; output?: unknown; error?: string },
  ): TaskValidationResult {
    const checks: Record<string, boolean> = {
      agentOk: agentResult.ok,
      hasOutput: agentResult.output !== undefined && agentResult.output !== null,
      workPackagePresent: Boolean(task.workPackage.goal),
    };

    // Soft file check — expected files listed in package
    if (task.workPackage.files.length > 0) {
      checks["filesDeclared"] = true;
    }

    // Role-specific validation expectations
    if (task.role === "qa" || task.role === "build") {
      checks["testsOrBuildSignal"] = agentResult.ok;
    }
    if (task.role === "review") {
      checks["reviewSignal"] = agentResult.ok;
    }

    const errors: string[] = [];
    if (!checks["agentOk"]) {
      errors.push(agentResult.error ?? "Agent reported failure");
    }
    if (!checks["hasOutput"]) {
      errors.push("Missing agent output");
    }

    return {
      ok: errors.length === 0,
      errors,
      checks,
    };
  }

  validatePlanComplete(tasks: readonly ExecutionTask[]): {
    ok: boolean;
    buildPassed: boolean;
    testsPassed: boolean;
  } {
    const build = tasks.find((t) => t.role === "build");
    const qa = tasks.find((t) => t.role === "qa");
    return {
      ok: tasks.every(
        (t) => t.status === "completed" || t.status === "skipped",
      ),
      buildPassed: !build || build.status === "completed",
      testsPassed: !qa || qa.status === "completed",
    };
  }
}

export function createExecutionValidator(): ExecutionValidator {
  return new ExecutionValidator();
}
