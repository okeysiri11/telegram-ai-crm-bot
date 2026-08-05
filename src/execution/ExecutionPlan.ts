import type {
  AgentRole,
  EngineeringSpecification,
  ExecutionEvent,
  ExecutionEventType,
  ExecutionPlanSnapshot,
  ExecutionTask,
  PlanStatus,
  TaskStatus,
} from "./types.js";
import { ROLE_TO_AGENT } from "./types.js";

export type ExecutionEventListener = (event: ExecutionEvent) => void;

/**
 * Mutable execution plan with graph snapshot helpers.
 */
export class ExecutionPlan {
  readonly id: string;
  readonly createdAt: string;
  readonly specification: EngineeringSpecification;
  status: PlanStatus = "draft";
  updatedAt: string;
  startedAt: string | null = null;
  completedAt: string | null = null;
  readonly tasks: ExecutionTask[] = [];
  private readonly listeners = new Set<ExecutionEventListener>();

  constructor(specification: EngineeringSpecification, id?: string) {
    this.id =
      id ??
      `plan_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
    this.createdAt = new Date().toISOString();
    this.updatedAt = this.createdAt;
    this.specification = specification;
  }

  on(listener: ExecutionEventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  emit(type: ExecutionEventType, payload: unknown): void {
    const event: ExecutionEvent = {
      type,
      at: new Date().toISOString(),
      payload,
    };
    for (const l of this.listeners) {
      try {
        l(event);
      } catch {
        /* ignore */
      }
    }
  }

  addTask(partial: {
    title: string;
    role: AgentRole;
    priority: number;
    dependencies: readonly string[];
    workPackage: ExecutionTask["workPackage"];
    parallelGroup?: number;
    id?: string;
  }): ExecutionTask {
    const id =
      partial.id ??
      `task_${this.tasks.length + 1}_${partial.role}`;
    const task: ExecutionTask = {
      id,
      planId: this.id,
      title: partial.title,
      role: partial.role,
      agentId: ROLE_TO_AGENT[partial.role],
      priority: partial.priority,
      dependencies: [...partial.dependencies],
      workPackage: partial.workPackage,
      status: partial.dependencies.length ? "blocked" : "ready",
      progress: 0,
      logs: [],
      ...(partial.parallelGroup !== undefined
        ? { parallelGroup: partial.parallelGroup }
        : {}),
    };
    this.tasks.push(task);
    this.touch();
    return task;
  }

  getTask(id: string): ExecutionTask | undefined {
    return this.tasks.find((t) => t.id === id);
  }

  setTaskStatus(id: string, status: TaskStatus): ExecutionTask {
    const task = this.getTask(id);
    if (!task) throw new Error(`Task not found: ${id}`);
    task.status = status;
    this.recomputeBlocked();
    this.touch();
    return task;
  }

  appendLog(id: string, message: string): void {
    const task = this.getTask(id);
    if (!task) return;
    task.logs.push(`${new Date().toISOString()} ${message}`);
  }

  recomputeBlocked(): void {
    for (const task of this.tasks) {
      if (task.status === "completed" || task.status === "failed" || task.status === "running" || task.status === "skipped") {
        continue;
      }
      const depsFailed = task.dependencies.some(
        (d) => this.getTask(d)?.status === "failed",
      );
      if (depsFailed) {
        task.status = "blocked";
        continue;
      }
      const depsDone = task.dependencies.every(
        (d) => this.getTask(d)?.status === "completed" || this.getTask(d)?.status === "skipped",
      );
      if (depsDone) {
        if (task.status === "blocked" || task.status === "pending") {
          task.status = "ready";
        }
      } else {
        task.status = "blocked";
      }
    }
  }

  snapshot(): ExecutionPlanSnapshot {
    const completed = this.tasks.filter((t) => t.status === "completed");
    const failed = this.tasks.filter((t) => t.status === "failed");
    const blocked = this.tasks.filter((t) => t.status === "blocked");
    const running = this.tasks.filter((t) => t.status === "running");
    const progress =
      this.tasks.length === 0
        ? 0
        : Math.round(
            ((completed.length + failed.length) / this.tasks.length) * 100,
          );
    const edges: Array<{ from: string; to: string }> = [];
    for (const t of this.tasks) {
      for (const d of t.dependencies) edges.push({ from: d, to: t.id });
    }
    return {
      id: this.id,
      status: this.status,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      startedAt: this.startedAt,
      completedAt: this.completedAt,
      specification: this.specification,
      tasks: this.tasks.map((t) => ({ ...t, logs: [...t.logs] })),
      graph: {
        nodes: this.tasks.map((t) => ({
          id: t.id,
          role: t.role,
          status: t.status,
        })),
        edges,
      },
      runningAgents: [...new Set(running.map((t) => t.agentId))],
      completedCount: completed.length,
      failedCount: failed.length,
      blockedCount: blocked.length,
      progress,
    };
  }

  touch(): void {
    this.updatedAt = new Date().toISOString();
  }
}

export function createExecutionPlan(
  specification: EngineeringSpecification,
): ExecutionPlan {
  return new ExecutionPlan(specification);
}
