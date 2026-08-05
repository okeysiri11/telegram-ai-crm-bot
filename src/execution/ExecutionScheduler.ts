import type { AiOrchestrator } from "@ados/orchestrator";
import type { ExecutionPlan } from "./ExecutionPlan.js";
import type { DependencyResolver } from "./DependencyResolver.js";
import type { ExecutionQueue } from "./ExecutionQueue.js";
import type { ExecutionValidator } from "./ExecutionValidator.js";
import type { ExecutionTask } from "./types.js";

/**
 * Schedules ready tasks and runs independent agents in parallel via Orchestrator.
 */
export class ExecutionScheduler {
  constructor(
    private readonly orchestrator: AiOrchestrator,
    private readonly resolver: DependencyResolver,
    private readonly queue: ExecutionQueue,
    private readonly validator: ExecutionValidator,
  ) {}

  async runPlan(plan: ExecutionPlan): Promise<void> {
    plan.status = "running";
    plan.startedAt = new Date().toISOString();
    plan.emit("plan.started", { planId: plan.id });
    this.queue.clear();
    this.queue.enqueueAll(plan.tasks);

    while (true) {
      plan.recomputeBlocked();
      const ready = this.resolver.readyTasks(plan);
      if (ready.length === 0) {
        const running = plan.tasks.some((t) => t.status === "running");
        if (running) {
          await delay(10);
          continue;
        }
        break;
      }

      // Parallel wave: all currently ready tasks
      plan.emit("task.assigned", {
        planId: plan.id,
        taskIds: ready.map((t) => t.id),
        agents: ready.map((t) => t.agentId),
      });

      await Promise.all(ready.map((task) => this.runTask(plan, task)));
    }

    const failed = plan.tasks.some((t) => t.status === "failed");
    const completed = plan.tasks.every(
      (t) =>
        t.status === "completed" ||
        t.status === "failed" ||
        t.status === "skipped",
    );
    plan.status = !completed
      ? "failed"
      : failed
        ? "partial"
        : "completed";
    plan.completedAt = new Date().toISOString();
    plan.touch();
    plan.emit("plan.completed", plan.snapshot());
  }

  private async runTask(
    plan: ExecutionPlan,
    task: ExecutionTask,
  ): Promise<void> {
    task.status = "running";
    task.progress = 10;
    task.startedAt = new Date().toISOString();
    plan.appendLog(task.id, `Assigned to ${task.agentId}`);
    plan.emit("task.started", { taskId: task.id, agentId: task.agentId });
    plan.touch();

    const started = Date.now();
    try {
      const result = await this.orchestrator.runAgent(task.agentId, {
        type: `execution.${task.role}`,
        task: task.title,
        payload: {
          workPackage: task.workPackage,
          planId: plan.id,
          role: task.role,
          specification: {
            mission: plan.specification.mission,
            objective: plan.specification.objective,
            acceptanceCriteria: plan.specification.acceptanceCriteria,
          },
        },
      });

      task.progress = 80;
      const validation = this.validator.validateTask(task, result);
      task.result = {
        agent: {
          ok: result.ok,
          agentId: result.agentId,
          durationMs: result.durationMs,
          output: result.output,
        },
        validation,
      };

      if (!result.ok || !validation.ok) {
        task.status = "failed";
        task.error =
          result.error ??
          (validation.errors.length
            ? validation.errors.join("; ")
            : "Validation failed");
        task.progress = 100;
        task.completedAt = new Date().toISOString();
        task.durationMs = Date.now() - started;
        plan.appendLog(task.id, `Failed: ${task.error}`);
        plan.emit("task.failed", { taskId: task.id, error: task.error });
        return;
      }

      task.status = "completed";
      task.progress = 100;
      task.completedAt = new Date().toISOString();
      task.durationMs = Date.now() - started;
      plan.appendLog(task.id, "Completed");
      plan.emit("task.completed", { taskId: task.id, agentId: task.agentId });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      task.status = "failed";
      task.error = message;
      task.progress = 100;
      task.completedAt = new Date().toISOString();
      task.durationMs = Date.now() - started;
      plan.appendLog(task.id, `Failed: ${message}`);
      plan.emit("task.failed", { taskId: task.id, error: message });
    } finally {
      plan.recomputeBlocked();
      plan.touch();
    }
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export function createExecutionScheduler(
  orchestrator: AiOrchestrator,
  resolver: DependencyResolver,
  queue: ExecutionQueue,
  validator: ExecutionValidator,
): ExecutionScheduler {
  return new ExecutionScheduler(orchestrator, resolver, queue, validator);
}
