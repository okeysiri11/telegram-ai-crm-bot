import type { ExecutionPlan } from "./ExecutionPlan.js";
import type { ExecutionTask } from "./types.js";

export interface DependencyAnalysis {
  readonly order: readonly string[];
  readonly parallelWaves: readonly (readonly string[])[];
  readonly blocked: readonly string[];
  readonly requiredAgents: readonly string[];
  readonly requiredResources: readonly string[];
}

/**
 * Resolves execution order, parallel waves, and blocked tasks.
 */
export class DependencyResolver {
  analyze(plan: ExecutionPlan): DependencyAnalysis {
    const tasks = plan.tasks;
    const order = topological(tasks);
    const waves: string[][] = [];
    const remaining = new Set(tasks.map((t) => t.id));
    const done = new Set<string>();

    while (remaining.size > 0) {
      const wave = [...remaining].filter((id) => {
        const t = plan.getTask(id)!;
        return t.dependencies.every((d) => done.has(d));
      });
      if (wave.length === 0) {
        // cycle or permanent block — emit remaining as blocked wave
        waves.push([...remaining]);
        break;
      }
      waves.push(wave);
      for (const id of wave) {
        remaining.delete(id);
        done.add(id);
      }
    }

    const blocked = tasks
      .filter((t) => t.status === "blocked")
      .map((t) => t.id);

    const requiredAgents = [...new Set(tasks.map((t) => t.agentId))];
    const requiredResources = [
      ...new Set(tasks.flatMap((t) => [...t.workPackage.files])),
    ];

    return {
      order,
      parallelWaves: waves,
      blocked,
      requiredAgents,
      requiredResources,
    };
  }

  readyTasks(plan: ExecutionPlan): ExecutionTask[] {
    plan.recomputeBlocked();
    return plan.tasks
      .filter((t) => t.status === "ready")
      .sort((a, b) => b.priority - a.priority);
  }
}

function topological(tasks: readonly ExecutionTask[]): string[] {
  const ids = new Set(tasks.map((t) => t.id));
  const indeg = new Map<string, number>();
  const children = new Map<string, string[]>();
  for (const t of tasks) {
    indeg.set(t.id, 0);
    children.set(t.id, []);
  }
  for (const t of tasks) {
    for (const d of t.dependencies) {
      if (!ids.has(d)) continue;
      indeg.set(t.id, (indeg.get(t.id) ?? 0) + 1);
      children.get(d)!.push(t.id);
    }
  }
  const queue = [...indeg.entries()]
    .filter(([, n]) => n === 0)
    .map(([id]) => id);
  const out: string[] = [];
  while (queue.length) {
    const id = queue.shift()!;
    out.push(id);
    for (const c of children.get(id) ?? []) {
      const next = (indeg.get(c) ?? 1) - 1;
      indeg.set(c, next);
      if (next === 0) queue.push(c);
    }
  }
  return out.length === tasks.length ? out : tasks.map((t) => t.id);
}

export function createDependencyResolver(): DependencyResolver {
  return new DependencyResolver();
}
