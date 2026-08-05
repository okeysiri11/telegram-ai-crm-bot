import type { ExecutionPlan } from "./ExecutionPlan.js";
import type { ExecutionReport, PlanStatus } from "./types.js";
import type { ExecutionValidator } from "./ExecutionValidator.js";

/**
 * Generates the final engineering execution report.
 */
export class ExecutionReporter {
  constructor(private readonly validator: ExecutionValidator) {}

  report(plan: ExecutionPlan): ExecutionReport {
    const completed = plan.tasks
      .filter((t) => t.status === "completed")
      .map((t) => t.title);
    const failed = plan.tasks
      .filter((t) => t.status === "failed")
      .map((t) => `${t.title}${t.error ? ` (${t.error})` : ""}`);
    const warnings: string[] = [];
    for (const t of plan.tasks) {
      if (t.status === "blocked") {
        warnings.push(`Blocked: ${t.title}`);
      }
      if (t.role === "deploy" && t.status === "skipped") {
        warnings.push("Deploy skipped");
      }
    }

    const planCheck = this.validator.validatePlanComplete(plan.tasks);
    const filesChanged = [
      ...new Set(plan.tasks.flatMap((t) => [...t.workPackage.files])),
    ];

    const nextRecommendations: string[] = [];
    if (failed.length) {
      nextRecommendations.push("Re-run failed tasks after fixing root causes");
      nextRecommendations.push("Inspect Orchestrator agent logs for failures");
    }
    if (!planCheck.buildPassed) {
      nextRecommendations.push("Fix build failures before deploy");
    }
    if (!planCheck.testsPassed) {
      nextRecommendations.push("Strengthen QA coverage for acceptance criteria");
    }
    if (planCheck.ok) {
      nextRecommendations.push("Merge and tag release candidate");
      nextRecommendations.push("Update Control Center demo narrative");
    }

    const status: PlanStatus = plan.status;
    const summary = [
      `Plan ${plan.id} → ${status}.`,
      `${completed.length} completed, ${failed.length} failed.`,
      `Build: ${planCheck.buildPassed ? "passed" : "failed/skipped"}.`,
      `Tests: ${planCheck.testsPassed ? "passed" : "failed/skipped"}.`,
    ].join(" ");

    return {
      planId: plan.id,
      generatedAt: new Date().toISOString(),
      status,
      completedTasks: completed,
      failedTasks: failed,
      warnings,
      buildStatus: planCheck.buildPassed
        ? "passed"
        : plan.tasks.some((t) => t.role === "build")
          ? "failed"
          : "skipped",
      testStatus: planCheck.testsPassed
        ? "passed"
        : plan.tasks.some((t) => t.role === "qa")
          ? "failed"
          : "skipped",
      filesChanged,
      nextRecommendations,
      summary,
    };
  }
}

export function createExecutionReporter(
  validator: ExecutionValidator,
): ExecutionReporter {
  return new ExecutionReporter(validator);
}
