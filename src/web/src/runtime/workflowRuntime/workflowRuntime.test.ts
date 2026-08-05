import { beforeEach, describe, expect, it } from "vitest";
import {
  WORKFLOW_RUNTIME_VERSION,
  workflowRuntime,
  workflowRegistry,
  workflowHistory,
  workflowSessions,
} from "@/runtime/workflowRuntime";
import { WORKFLOW_HISTORY_KEY } from "@/runtime/workflowRuntime/workflowHistory";
import { WORKFLOW_PERSIST_KEY } from "@/runtime/workflowRuntime/workflowTypes";
import { commandRuntime } from "@/runtime/commandRuntime";

describe("Sprint 28.8 Workflow Runtime", () => {
  beforeEach(() => {
    try {
      localStorage.removeItem(WORKFLOW_HISTORY_KEY);
      localStorage.removeItem(WORKFLOW_PERSIST_KEY);
    } catch {
      /* ignore */
    }
    commandRuntime.startup();
    workflowRuntime.startup();
  });

  it("boots with seed definitions including templates and demos", () => {
    const snap = workflowRuntime.startup();
    expect(WORKFLOW_RUNTIME_VERSION).toBe("28.8");
    expect(snap.definitions).toBeGreaterThan(5);
    expect(workflowRegistry.get("demo_parallel_ops")).toBeTruthy();
    expect(workflowRegistry.get("tpl_new_client")).toBeTruthy();
    expect(workflowRegistry.get("demo_approval_gate")).toBeTruthy();
  });

  it("starts, completes parallel demo, and records history", async () => {
    const res = await workflowRuntime.start("demo_parallel_ops", { surface: "test" });
    expect(res.ok).toBe(true);
    expect(res.sessionId).toBeTruthy();
    const session = workflowRuntime.getSession(res.sessionId!);
    expect(session?.status === "completed" || session?.status === "running").toBe(true);
    // allow async settle
    await new Promise((r) => setTimeout(r, 10));
    const live = workflowRuntime.getSession(res.sessionId!);
    expect(["completed", "running", "waiting"]).toContain(live?.status);
  });

  it("pauses approval workflow and resumes with approve", async () => {
    const res = await workflowRuntime.start("demo_approval_gate");
    expect(res.ok).toBe(true);
    const s = workflowRuntime.getSession(res.sessionId!);
    expect(s?.status).toBe("paused");
    expect(s?.approvalPending).toBe(true);
    const resumed = await workflowRuntime.approve(res.sessionId!, true);
    expect(resumed.ok).toBe(true);
    expect(resumed.session?.status === "completed" || resumed.session?.status === "running").toBe(true);
  });

  it("cancels a waiting wait_event workflow", async () => {
    const res = await workflowRuntime.start("demo_wait_event");
    expect(res.ok).toBe(true);
    const s = workflowRuntime.getSession(res.sessionId!);
    expect(s?.status).toBe("waiting");
    const cancelled = workflowRuntime.cancel(res.sessionId!);
    expect(cancelled.ok).toBe(true);
    expect(cancelled.session?.status).toBe("cancelled");
    expect(workflowHistory.list(5).some((h) => h.sessionId === res.sessionId)).toBe(true);
  });

  it("starts workflows via Command Runtime start_workflow", async () => {
    const cmd = await commandRuntime.execute("start_workflow", { workflowId: "demo_parallel_ops" });
    expect(cmd.ok).toBe(true);
  });

  it("exposes inspector snapshot and stats", () => {
    const snap = workflowRuntime.inspectorSnapshot();
    expect(snap.definitions.length).toBeGreaterThan(0);
    expect(snap.stats.version).toBe("28.8");
    expect(workflowSessions.list().length).toBeGreaterThanOrEqual(0);
  });
});
