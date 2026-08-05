import { describe, expect, it, beforeEach } from "vitest";
import { createAiOrchestrator } from "@ados/orchestrator";
import {
  createExecutionPlanner,
  createExecutionService,
  createTaskAnalyzer,
  EXECUTION_SERVICE_ID,
} from "../index.js";

const SAMPLE_SPEC = {
  mission: "Ship Execution Planner module",
  objective: "Turn ChatGPT specs into agent work packages",
  requirements: [
    "Parse engineering specification",
    "Split tasks across agents",
    "Run parallel waves",
  ],
  files: [
    "src/execution/ExecutionPlanner.ts",
    "platform_console/src/pages/ExecutionPlannerPage.tsx",
  ],
  modules: ["src/execution", "platform_console"],
  tests: ["unit tests", "integration tests"],
  acceptanceCriteria: [
    "POST /execution/plan works",
    "Report includes build and test status",
  ],
};

describe("TaskAnalyzer", () => {
  it("detects UI and QA signals", () => {
    const a = createTaskAnalyzer().analyze(SAMPLE_SPEC);
    expect(a.needsDeveloper).toBe(true);
    expect(a.needsUi).toBe(true);
    expect(a.needsQa).toBe(true);
    expect(a.needsReview).toBe(true);
    expect(a.needsBuild).toBe(true);
  });
});

describe("ExecutionPlanner", () => {
  const orch = createAiOrchestrator();

  beforeEach(() => {
    orch.registry.clear();
    orch.stop();
    orch.start(true);
  });

  it("creates plan, runs parallel waves via Orchestrator, reports", async () => {
    const planner = createExecutionPlanner({
      orchestrator: orch,
      autoRun: true,
    });
    const events: string[] = [];
    planner.on((e) => events.push(e.type));

    const result = await planner.plan(SAMPLE_SPEC);
    expect(result.plan.tasks.length).toBeGreaterThanOrEqual(5);
    expect(result.analysis.parallelWaves.length).toBeGreaterThanOrEqual(2);
    expect(["completed", "partial"]).toContain(result.plan.status);
    expect(result.report).toBeTruthy();
    expect(result.report!.completedTasks.length).toBeGreaterThan(0);
    expect(events).toContain("plan.created");
    expect(events).toContain("plan.started");
    expect(events).toContain("plan.completed");

    const status = planner.status();
    expect(status.currentPlan?.id).toBe(result.plan.id);
    expect(planner.listHistory().length).toBeGreaterThan(0);
  }, 30_000);

  it("can plan without auto-run then run", async () => {
    const planner = createExecutionPlanner({
      orchestrator: orch,
      autoRun: false,
    });
    const created = await planner.plan(SAMPLE_SPEC, { autoRun: false });
    expect(created.plan.status).toBe("ready");
    expect(created.report).toBeNull();
    const report = await planner.run();
    expect(report.planId).toBe(created.plan.id);
  }, 30_000);

  it("ExecutionService registers as ados.execution", async () => {
    const svc = createExecutionService({ orchestrator: orch });
    expect(svc.id).toBe(EXECUTION_SERVICE_ID);
    await svc.initialize();
    await svc.start();
    expect(svc.health().status).toBe("healthy");
    await svc.stop();
  });
});
