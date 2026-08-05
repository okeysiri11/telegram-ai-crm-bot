import type { ContextArtifact } from "./types.js";

/**
 * Shared enterprise memory for one collaboration workflow.
 * Survives the full run; agents read/append via Orchestrator only.
 */
export class SharedWorkflowContext {
  readonly workflowId: string;
  private readonly data = new Map<string, unknown>();
  private readonly artifacts: ContextArtifact[] = [];
  private readonly decisions: Array<{
    at: string;
    agentId?: string;
    decision: string;
    data?: unknown;
  }> = [];
  private readonly prompts: Array<{
    at: string;
    agentId?: string;
    prompt: string;
  }> = [];
  private readonly logs: Array<{ at: string; agentId?: string; message: string }> =
    [];

  constructor(workflowId: string, seed?: Readonly<Record<string, unknown>>) {
    this.workflowId = workflowId;
    if (seed) {
      for (const [k, v] of Object.entries(seed)) {
        this.data.set(k, v);
      }
    }
  }

  get<T = unknown>(key: string): T | undefined {
    return this.data.get(key) as T | undefined;
  }

  set(key: string, value: unknown): void {
    this.data.set(key, value);
  }

  append(key: string, value: unknown): void {
    const prev = this.data.get(key);
    if (Array.isArray(prev)) {
      this.data.set(key, [...prev, value]);
    } else if (prev === undefined) {
      this.data.set(key, [value]);
    } else {
      this.data.set(key, [prev, value]);
    }
  }

  storeArtifact(
    artifact: Omit<ContextArtifact, "id" | "at"> & { id?: string; at?: string },
  ): ContextArtifact {
    const full: ContextArtifact = {
      id:
        artifact.id ??
        `art_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
      at: artifact.at ?? new Date().toISOString(),
      kind: artifact.kind,
      name: artifact.name,
      data: artifact.data,
      ...(artifact.agentId !== undefined ? { agentId: artifact.agentId } : {}),
    };
    this.artifacts.push(full);
    this.append("artifacts", full.id);
    return full;
  }

  storeDecision(decision: string, agentId?: string, data?: unknown): void {
    this.decisions.push({
      at: new Date().toISOString(),
      decision,
      ...(agentId !== undefined ? { agentId } : {}),
      ...(data !== undefined ? { data } : {}),
    });
    this.set("lastDecision", decision);
  }

  storePrompt(prompt: string, agentId?: string): void {
    this.prompts.push({
      at: new Date().toISOString(),
      prompt,
      ...(agentId !== undefined ? { agentId } : {}),
    });
  }

  storeLog(message: string, agentId?: string): void {
    this.logs.push({
      at: new Date().toISOString(),
      message,
      ...(agentId !== undefined ? { agentId } : {}),
    });
  }

  keys(): string[] {
    return [...this.data.keys()];
  }

  entries(): Record<string, unknown> {
    return Object.fromEntries(this.data.entries());
  }

  listArtifacts(): ContextArtifact[] {
    return [...this.artifacts];
  }

  snapshot(): {
    workflowId: string;
    data: Record<string, unknown>;
    artifacts: ContextArtifact[];
    decisions: Array<{
      at: string;
      agentId?: string;
      decision: string;
      data?: unknown;
    }>;
    prompts: Array<{ at: string; agentId?: string; prompt: string }>;
    logs: Array<{ at: string; agentId?: string; message: string }>;
  } {
    return {
      workflowId: this.workflowId,
      data: this.entries(),
      artifacts: this.listArtifacts(),
      decisions: [...this.decisions],
      prompts: [...this.prompts],
      logs: [...this.logs],
    };
  }
}
