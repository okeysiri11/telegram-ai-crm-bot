import type { ExecutionTask, TaskStatus } from "./types.js";

/**
 * Priority queue of execution tasks by status.
 */
export class ExecutionQueue {
  private readonly byId = new Map<string, ExecutionTask>();

  enqueue(task: ExecutionTask): void {
    this.byId.set(task.id, task);
  }

  enqueueAll(tasks: readonly ExecutionTask[]): void {
    for (const t of tasks) this.enqueue(t);
  }

  get(id: string): ExecutionTask | undefined {
    return this.byId.get(id);
  }

  list(status?: TaskStatus): ExecutionTask[] {
    const all = [...this.byId.values()].sort(
      (a, b) => b.priority - a.priority,
    );
    return status ? all.filter((t) => t.status === status) : all;
  }

  ready(): ExecutionTask[] {
    return this.list("ready");
  }

  running(): ExecutionTask[] {
    return this.list("running");
  }

  clear(): void {
    this.byId.clear();
  }

  snapshot() {
    const all = this.list();
    return {
      total: all.length,
      ready: all.filter((t) => t.status === "ready").length,
      running: all.filter((t) => t.status === "running").length,
      blocked: all.filter((t) => t.status === "blocked").length,
      completed: all.filter((t) => t.status === "completed").length,
      failed: all.filter((t) => t.status === "failed").length,
    };
  }
}

export function createExecutionQueue(): ExecutionQueue {
  return new ExecutionQueue();
}
