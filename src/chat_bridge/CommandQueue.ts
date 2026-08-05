import type { ChatTask, ChatTaskStatus } from "./types.js";

/**
 * Persistent in-memory command queue for ChatGPT bridge tasks.
 * Statuses: Queued → Running → Waiting|Review → Done|Failed|Cancelled|PartialSuccess
 */
export class CommandQueue {
  private readonly tasks = new Map<string, ChatTask>();
  private readonly order: string[] = [];

  enqueue(task: ChatTask): ChatTask {
    this.tasks.set(task.id, task);
    this.order.push(task.id);
    return task;
  }

  get(id: string): ChatTask | undefined {
    return this.tasks.get(id);
  }

  update(id: string, patch: Partial<ChatTask>): ChatTask {
    const task = this.tasks.get(id);
    if (!task) throw new Error(`Task not found: ${id}`);
    Object.assign(task, patch, { updatedAt: new Date().toISOString() });
    return task;
  }

  setStatus(id: string, status: ChatTaskStatus): ChatTask {
    return this.update(id, { status });
  }

  list(filter?: { status?: ChatTaskStatus }): ChatTask[] {
    const all = this.order
      .map((id) => this.tasks.get(id))
      .filter((t): t is ChatTask => Boolean(t))
      .sort((a, b) => b.priority - a.priority);
    if (!filter?.status) return all;
    return all.filter((t) => t.status === filter.status);
  }

  snapshot() {
    const all = this.list();
    return {
      total: all.length,
      queued: all.filter((t) => t.status === "Queued").length,
      running: all.filter((t) => t.status === "Running").length,
      waiting: all.filter((t) => t.status === "Waiting").length,
      review: all.filter((t) => t.status === "Review").length,
      done: all.filter((t) => t.status === "Done").length,
      failed: all.filter((t) => t.status === "Failed").length,
      cancelled: all.filter((t) => t.status === "Cancelled").length,
      tasks: all,
    };
  }

  nextQueued(): ChatTask | undefined {
    return this.list({ status: "Queued" })[0];
  }
}

export function createCommandQueue(): CommandQueue {
  return new CommandQueue();
}
