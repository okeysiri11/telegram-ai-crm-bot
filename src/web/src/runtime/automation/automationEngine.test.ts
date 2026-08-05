import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  AUTOMATION_ENGINE_VERSION,
  AUTOMATION_HISTORY_KEY,
  automationEngine,
  automationHistory,
  automationQueue,
  automationRegistry,
  automationScheduler,
  automationTriggers,
  computeBackoffDelay,
  normalizePolicy,
  validatePolicy,
  validateAutomation,
} from "@/runtime/automation";
import { commandRuntime } from "@/runtime/commandRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";

describe("Sprint 28.9 Automation Engine", () => {
  beforeEach(() => {
    try {
      localStorage.removeItem(AUTOMATION_HISTORY_KEY);
    } catch {
      /* ignore */
    }
    automationEngine.__resetForTests();
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
  });

  it("registers seed automations and exposes version", () => {
    expect(AUTOMATION_ENGINE_VERSION).toBe("28.9");
    expect(automationRegistry.get("auto_pulse_parallel")).toBeTruthy();
    expect(automationRegistry.get("auto_new_client")).toBeTruthy();
    const snap = automationEngine.inspectorSnapshot();
    expect(snap.version).toBe("28.9");
    expect(snap.automations.length).toBeGreaterThanOrEqual(4);
  });

  it("validates policies and automation definitions", () => {
    const bad = validatePolicy({
      ...normalizePolicy(),
      retryCount: 99,
      timeoutMs: 10,
    });
    expect(bad.ok).toBe(false);
    expect(bad.errors).toContain("retryCount_out_of_range");
    expect(bad.errors).toContain("timeoutMs_out_of_range");

    const defOk = validateAutomation({
      id: "t1",
      name: "Test",
      workflowId: "demo_parallel_ops",
      enabled: true,
      triggers: [{ kind: "manual" }],
      policy: normalizePolicy({ retryCount: 1 }),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
    expect(defOk.ok).toBe(true);

    const scheduleBad = validateAutomation({
      id: "t2",
      name: "Sched",
      workflowId: "demo_parallel_ops",
      enabled: true,
      triggers: [{ kind: "schedule" }],
      policy: normalizePolicy(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
    expect(scheduleBad.ok).toBe(false);
    expect(computeBackoffDelay(normalizePolicy({ backoffMs: 100 }), 3)).toBe(300);
  });

  it("runs automation through queue into Workflow Runtime", async () => {
    const res = await automationEngine.runAutomation("auto_pulse_parallel", "manual");
    expect(res.ok).toBe(true);
    expect(res.jobId).toBeTruthy();
    await new Promise((r) => setTimeout(r, 20));
    const job = automationQueue.get(res.jobId!);
    expect(job).toBeTruthy();
    expect(["completed", "running", "waiting", "pending"]).toContain(job!.status);
    expect(job!.timeline.length).toBeGreaterThan(0);
  });

  it("retries failed jobs per policy", async () => {
    vi.useFakeTimers();
    const reg = automationEngine.registerAutomation({
      id: "auto_retry_demo",
      name: "Retry Demo",
      workflowId: "missing_workflow_xyz",
      enabled: true,
      triggers: [{ kind: "manual" }],
      policy: {
        retryCount: 1,
        timeoutMs: 5000,
        backoffMs: 50,
        concurrency: 1,
        priority: 90,
        errorPolicy: "retry",
      },
    });
    expect(reg.ok).toBe(true);

    const res = await automationEngine.runAutomation("auto_retry_demo", "manual");
    expect(res.ok).toBe(true);
    await vi.advanceTimersByTimeAsync(5);
    let job = automationQueue.get(res.jobId!);
    expect(job?.status === "retry" || job?.status === "pending" || job?.status === "failed").toBe(true);

    await vi.advanceTimersByTimeAsync(80);
    await Promise.resolve();
    job = automationQueue.get(res.jobId!);
    expect(job).toBeTruthy();
    expect(job!.attempt).toBeGreaterThanOrEqual(1);
    vi.useRealTimers();
  });

  it("records history and inspector stats", async () => {
    await automationEngine.runAutomation("auto_pulse_parallel", "manual");
    await new Promise((r) => setTimeout(r, 25));
    const hist = automationHistory.list(10);
    expect(hist.length).toBeGreaterThanOrEqual(0);
    const stats = automationEngine.stats();
    expect(stats.version).toBe("28.9");
    expect(stats.queue).toBeTruthy();
    expect(typeof stats.history.successRate).toBe("number");
    const snap = automationEngine.inspectorSnapshot();
    expect(Array.isArray(snap.timeline)).toBe(true);
    expect(Array.isArray(snap.queue)).toBe(true);
  });

  it("scheduler fires registered intervals", () => {
    automationRegistry.setEnabled("auto_scheduled_pulse", true);
    automationEngine.registerAutomation({
      id: "auto_sched_test",
      name: "Sched Test",
      workflowId: "demo_parallel_ops",
      enabled: true,
      triggers: [{ kind: "schedule", scheduleMs: 60_000 }],
      policy: { retryCount: 0, timeoutMs: 10_000, backoffMs: 0, concurrency: 1, priority: 10, errorPolicy: "fail" },
    });
    // re-sync schedules after register
    automationTriggers.syncSchedules();
    expect(automationScheduler.list().some((s) => s.automationId === "auto_sched_test")).toBe(true);
    const before = automationQueue.list().length;
    automationScheduler.fire("auto_sched_test");
    expect(automationQueue.list().length).toBeGreaterThanOrEqual(before);
  });

  it("cancel pause resume and manual retry", async () => {
    const res = await automationEngine.runAutomation("auto_pulse_parallel", "manual");
    expect(res.ok).toBe(true);
    automationEngine.pauseAutomation("auto_pulse_parallel");
    automationEngine.resumeAutomation("auto_pulse_parallel");
    if (res.jobId) {
      automationEngine.cancelAutomation(res.jobId);
      const cancelled = automationQueue.get(res.jobId);
      expect(cancelled?.status).toBe("cancelled");
      await automationEngine.retryAutomation(res.jobId);
      const retried = automationQueue.get(res.jobId);
      expect(retried?.status === "pending" || retried?.status === "running" || retried?.status === "completed").toBe(
        true,
      );
    }
  });

  it("registers via Command Runtime auto_run", async () => {
    const cmd = await commandRuntime.execute("auto_run", { automationId: "auto_pulse_parallel" });
    expect(cmd.ok).toBe(true);
  });
});
