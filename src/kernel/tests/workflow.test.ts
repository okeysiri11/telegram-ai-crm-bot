import { describe, expect, it, beforeEach, afterEach } from "vitest";
import {
  createWorkflowEngine,
  createEnterpriseDeliveryWorkflow,
  WorkflowEngine,
  WorkflowValidator,
  WorkflowDefinition,
} from "../workflow/index.js";
import { createKernel } from "../Kernel.js";

describe("WorkflowValidator", () => {
  it("rejects missing start", () => {
    const def = WorkflowDefinition.create({
      id: "bad",
      version: "1.0.0",
      start: "missing",
      steps: [{ id: "a", kind: "task", handlerId: "h", next: [] }],
    });
    const issues = new WorkflowValidator().validate(def);
    expect(issues.some((i) => i.level === "error")).toBe(true);
  });
});

describe("WorkflowEngine", () => {
  let engine: WorkflowEngine;

  beforeEach(() => {
    engine = createWorkflowEngine();
    engine.registerHandler("ok", async (ctx) => {
      const n = (ctx.get<number>("n") ?? 0) + 1;
      ctx.set("n", n);
      return n;
    });
    engine.registerHandler("fail", async () => {
      throw new Error("boom");
    });
    engine.registerHandler("compensate", async (ctx) => {
      ctx.set("compensated", true);
      return true;
    });
  });

  afterEach(() => {
    engine.dispose();
  });

  it("runs sequential workflows", async () => {
    engine.register({
      id: "seq",
      version: "1.0.0",
      start: "a",
      steps: [
        { id: "a", kind: "task", handlerId: "ok", next: ["b"] },
        { id: "b", kind: "task", handlerId: "ok", next: [] },
      ],
    });
    const inst = await engine.start("seq", { input: { n: 0 } });
    expect(inst.status).toBe("Completed");
    expect(inst.context.get("n")).toBe(2);
    expect(engine.history(inst.id).some((h) => h.type === "WorkflowFinished")).toBe(
      true,
    );
  });

  it("runs parallel branches then joins", async () => {
    const seen: string[] = [];
    engine.registerHandler("branch", async (ctx, _input) => {
      // identity from step output key set by executor using step id — use a counter
      seen.push("x");
      return true;
    });
    engine.registerHandler("join", async () => {
      seen.push("join");
      return true;
    });
    engine.register({
      id: "par",
      version: "1.0.0",
      start: "fork",
      steps: [
        { id: "fork", kind: "parallel", next: ["l", "r"] },
        { id: "l", kind: "task", handlerId: "branch", next: ["join"] },
        { id: "r", kind: "task", handlerId: "branch", next: ["join"] },
        { id: "join", kind: "task", handlerId: "join", next: [] },
      ],
    });
    const inst = await engine.start("par");
    expect(inst.status).toBe("Completed");
    expect(seen.filter((s) => s === "x")).toHaveLength(2);
    expect(seen).toContain("join");
  });

  it("retries then succeeds", async () => {
    let attempts = 0;
    engine.registerHandler("flaky", async () => {
      attempts += 1;
      if (attempts < 3) throw new Error("not yet");
      return "ok";
    });
    engine.register({
      id: "retry",
      version: "1.0.0",
      start: "t",
      steps: [
        {
          id: "t",
          kind: "task",
          handlerId: "flaky",
          retry: { maxAttempts: 3, backoffMs: 1 },
          next: [],
        },
      ],
    });
    const inst = await engine.start("retry");
    expect(inst.status).toBe("Completed");
    expect(attempts).toBe(3);
  });

  it("runs compensation rollback on failure", async () => {
    engine.register({
      id: "rb",
      version: "1.0.0",
      start: "a",
      steps: [
        {
          id: "a",
          kind: "task",
          handlerId: "ok",
          next: ["b"],
          compensateWith: "ca",
        },
        { id: "b", kind: "task", handlerId: "fail", next: [] },
        {
          id: "ca",
          kind: "compensation",
          handlerId: "compensate",
          next: [],
        },
      ],
    });
    const inst = await engine.start("rb", { input: { n: 0 } });
    expect(inst.status).toBe("Compensated");
    expect(inst.context.get("compensated")).toBe(true);
    expect(
      engine.history(inst.id).some((h) => h.type === "CompensationCompleted"),
    ).toBe(true);
  });

  it("supports approval gates", async () => {
    engine.register({
      id: "appr",
      version: "1.0.0",
      start: "gate",
      steps: [
        {
          id: "gate",
          kind: "approval",
          approvalRole: "CEO",
          next: ["done"],
        },
        { id: "done", kind: "task", handlerId: "ok", next: [] },
      ],
    });
    let inst = await engine.start("appr", { input: { n: 0 } });
    expect(inst.status).toBe("WaitingApproval");
    inst = await engine.approve(inst.id, "gate", {
      approved: true,
      actor: "CEO",
    });
    expect(inst.status).toBe("Completed");
  });

  it("supports conditional branching", async () => {
    engine.register({
      id: "cond",
      version: "1.0.0",
      start: "c",
      steps: [
        {
          id: "c",
          kind: "condition",
          condition: (ctx) => ctx.get<boolean>("go") === true,
          whenTrue: "yes",
          whenFalse: "no",
        },
        { id: "yes", kind: "task", handlerId: "ok", next: [] },
        { id: "no", kind: "task", handlerId: "ok", next: [] },
      ],
    });
    const inst = await engine.start("cond", { input: { go: true, n: 0 } });
    expect(inst.status).toBe("Completed");
    expect(inst.completedSteps).toContain("yes");
    expect(inst.completedSteps).not.toContain("no");
  });

  it("runs enterprise delivery example through approval", async () => {
    const def = createEnterpriseDeliveryWorkflow();
    for (const id of [
      "agent.architect",
      "agent.backend",
      "agent.database",
      "agent.frontend",
      "agent.qa",
      "agent.docs",
      "agent.knowledge",
      "agent.devops",
      "agent.release",
      "agent.architect.compensate",
    ]) {
      engine.registerHandler(id, async () => true);
    }
    engine.register(def);
    let inst = await engine.start(def.id);
    expect(inst.status).toBe("WaitingApproval");
    expect(inst.waitingApprovalStepId).toBe("approval.release");
    inst = await engine.approve(inst.id, "approval.release", {
      approved: true,
    });
    expect(inst.status).toBe("Completed");
    expect(inst.completedSteps).toContain("database");
    expect(inst.completedSteps).toContain("frontend");
    expect(inst.completedSteps).toContain("release");
  });
});

describe("Kernel + Workflow Engine", () => {
  it("exposes workflow engine wired to bus and mesh", async () => {
    const kernel = createKernel({ config: { environment: "test" } });
    await kernel.start();
    expect(kernel.workflowEngine).toBeTruthy();
    kernel.workflowEngine.registerHandler("ping", async () => "pong");
    kernel.workflowEngine.register({
      id: "k.wf",
      version: "1.0.0",
      start: "t",
      steps: [{ id: "t", kind: "task", handlerId: "ping", next: [] }],
    });
    const inst = await kernel.workflowEngine.start("k.wf");
    expect(inst.status).toBe("Completed");
    await kernel.dispose();
  });
});
