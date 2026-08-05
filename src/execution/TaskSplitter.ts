import type { ExecutionPlan } from "./ExecutionPlan.js";
import type { AnalyzedSpec } from "./TaskAnalyzer.js";
import type { AgentRole, WorkPackage } from "./types.js";

/**
 * Splits analyzed specs into role-based work packages (execution only).
 */
export class TaskSplitter {
  split(plan: ExecutionPlan, analyzed: AnalyzedSpec): void {
    const spec = analyzed.specification;
    const files = [...spec.files];
    const modules = [...spec.modules];

    const ids: Partial<Record<AgentRole, string>> = {};

    if (analyzed.needsDeveloper) {
      const id = "task_developer";
      ids.developer = id;
      plan.addTask({
        id,
        title: `Implement: ${spec.objective}`,
        role: "developer",
        priority: 9,
        dependencies: [],
        parallelGroup: 1,
        workPackage: wp(
          spec.mission,
          `Implement requirements for ${spec.objective}`,
          files,
          "Code and modules updated per requirements",
          [
            "Files modified as listed",
            ...spec.acceptanceCriteria.slice(0, 3),
          ],
        ),
      });
    }

    if (analyzed.needsUi) {
      const id = "task_ui";
      ids.ui = id;
      plan.addTask({
        id,
        title: `UI: ${spec.objective}`,
        role: "ui",
        priority: 8,
        dependencies: [],
        parallelGroup: 1,
        workPackage: wp(
          spec.mission,
          `Deliver UI surfaces for ${spec.objective}`,
          files.filter((f) => /\.(tsx|jsx|css|html)$/i.test(f)).length
            ? files.filter((f) => /\.(tsx|jsx|css|html)$/i.test(f))
            : files,
          "UI components/pages ready",
          ["UI compiles", "Control Center patterns preserved"],
        ),
      });
    }

    if (analyzed.needsDocs) {
      const id = "task_documentation";
      ids.documentation = id;
      plan.addTask({
        id,
        title: `Document: ${spec.objective}`,
        role: "documentation",
        priority: 5,
        dependencies: [],
        parallelGroup: 1,
        workPackage: wp(
          spec.mission,
          `Document modules ${modules.join(", ") || "and APIs"}`,
          files.filter((f) => /\.md$/i.test(f)),
          "Documentation updated",
          ["Docs describe mission, APIs, acceptance"],
        ),
      });
    }

    // Review depends on developer (+ ui if present)
    const reviewDeps = [ids.developer, ids.ui].filter(
      (x): x is string => Boolean(x),
    );
    const reviewId = "task_review";
    ids.review = reviewId;
    plan.addTask({
      id: reviewId,
      title: `Review: ${spec.objective}`,
      role: "review",
      priority: 7,
      dependencies: reviewDeps,
      parallelGroup: 2,
      workPackage: wp(
        spec.mission,
        "Review implementation against acceptance criteria",
        files,
        "Review findings recorded",
        ["No critical defects", ...spec.acceptanceCriteria.slice(0, 2)],
      ),
    });

    if (analyzed.needsQa) {
      const qaId = "task_qa";
      ids.qa = qaId;
      plan.addTask({
        id: qaId,
        title: `QA: ${spec.objective}`,
        role: "qa",
        priority: 7,
        dependencies: reviewDeps,
        parallelGroup: 2,
        workPackage: wp(
          spec.mission,
          `Validate tests: ${spec.tests.join(", ") || "unit/integration"}`,
          files,
          "Tests passed",
          spec.tests.length ? [...spec.tests] : ["Test suite green"],
        ),
      });
    }

    const buildDeps = [reviewId, ids.qa].filter(
      (x): x is string => Boolean(x),
    );
    const buildId = "task_build";
    ids.build = buildId;
    plan.addTask({
      id: buildId,
      title: `Build: ${spec.objective}`,
      role: "build",
      priority: 6,
      dependencies: buildDeps,
      parallelGroup: 3,
      workPackage: wp(
        spec.mission,
        "Run production build",
        [],
        "Build passed",
        ["npm run build succeeds"],
      ),
    });

    if (analyzed.needsDeploy) {
      plan.addTask({
        id: "task_deploy",
        title: `Deploy: ${spec.objective}`,
        role: "deploy",
        priority: 4,
        dependencies: [buildId],
        parallelGroup: 4,
        workPackage: wp(
          spec.mission,
          "Prepare deployment artifacts / checklist",
          [],
          "Deploy readiness confirmed",
          ["Build artifacts available", "Rollback path noted"],
        ),
      });
    }

    plan.recomputeBlocked();
    plan.status = "ready";
    plan.touch();
  }
}

function wp(
  mission: string,
  goal: string,
  files: readonly string[],
  expectedResult: string,
  validation: readonly string[],
): WorkPackage {
  return { mission, goal, files, expectedResult, validation };
}

export function createTaskSplitter(): TaskSplitter {
  return new TaskSplitter();
}
