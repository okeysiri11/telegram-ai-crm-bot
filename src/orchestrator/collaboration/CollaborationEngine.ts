import type { AiOrchestrator } from "../AiOrchestrator.js";
import { SharedWorkflowContext } from "./SharedContext.js";
import { CollaborationTimeline } from "./Timeline.js";
import {
  getWorkflowTemplate,
  listWorkflowTemplates,
} from "./templates.js";
import type {
  CollaborationStepDef,
  CollaborationStepState,
  CollaborationWorkflowSnapshot,
  CollaborationWorkflowStatus,
  WorkflowTemplate,
} from "./types.js";

export type CollaborationListener = (event: {
  type: string;
  payload: unknown;
}) => void;

interface CollaborationRun {
  id: string;
  template: WorkflowTemplate;
  status: CollaborationWorkflowStatus;
  priority: number;
  createdAt: string;
  updatedAt: string;
  startedAt: number;
  context: SharedWorkflowContext;
  steps: CollaborationStepState[];
  currentStepIds: string[];
  pauseRequested: boolean;
  cancelRequested: boolean;
  resumeGate: Promise<void> | null;
  resumeResolve: (() => void) | null;
  runPromise: Promise<void> | null;
}

/**
 * Multi-Agent Collaboration Engine.
 * All agent work is dispatched through AiOrchestrator — never peer-to-peer.
 */
export class CollaborationEngine {
  readonly timeline = new CollaborationTimeline();
  private readonly runs = new Map<string, CollaborationRun>();
  private readonly listeners = new Set<CollaborationListener>();
  private seq = 0;

  constructor(private readonly orchestrator: AiOrchestrator) {}

  on(listener: CollaborationListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  listTemplates(): readonly WorkflowTemplate[] {
    return listWorkflowTemplates();
  }

  async start(input: {
    templateId?: string;
    name?: string;
    payload?: unknown;
    priority?: number;
  }): Promise<CollaborationWorkflowSnapshot> {
    const templateId = input.templateId ?? "tpl.crm_generation";
    const template = getWorkflowTemplate(templateId);
    if (!template) throw new Error(`Unknown workflow template: ${templateId}`);

    const id = this.nextId();
    const createdAt = new Date().toISOString();
    const context = new SharedWorkflowContext(id, {
      goal: input.name ?? template.name,
      input: input.payload ?? {},
      templateId: template.id,
    });

    const steps: CollaborationStepState[] = template.steps.map((s) => ({
      id: s.id,
      agentId: s.agentId,
      status: "pending",
      attempts: 0,
    }));

    const run: CollaborationRun = {
      id,
      template,
      status: "Created",
      priority: input.priority ?? template.priority ?? 5,
      createdAt,
      updatedAt: createdAt,
      startedAt: Date.now(),
      context,
      steps,
      currentStepIds: [],
      pauseRequested: false,
      cancelRequested: false,
      resumeGate: null,
      resumeResolve: null,
      runPromise: null,
    };
    this.runs.set(id, run);

    this.emitTimeline(run, "workflow.started", {
      message: `Started ${template.name}`,
    });
    this.emit("workflow.started", this.snapshot(run));

    run.status = "Running";
    run.runPromise = this.executeRun(run).catch((error) => {
      run.status = "Failed";
      run.updatedAt = new Date().toISOString();
      const message = error instanceof Error ? error.message : String(error);
      this.emitTimeline(run, "workflow.failed", { error: message });
      this.emit("workflow.failed", { id: run.id, error: message });
    });

    return this.snapshot(run);
  }

  get(id: string): CollaborationWorkflowSnapshot | undefined {
    const run = this.runs.get(id);
    return run ? this.snapshot(run) : undefined;
  }

  list(): CollaborationWorkflowSnapshot[] {
    return [...this.runs.values()]
      .sort((a, b) => b.priority - a.priority || b.startedAt - a.startedAt)
      .map((r) => this.snapshot(r));
  }

  history(limit = 100): CollaborationWorkflowSnapshot[] {
    return this.list().slice(0, limit);
  }

  getContext(workflowId: string) {
    const run = this.require(workflowId);
    return run.context.snapshot();
  }

  listMemory() {
    return this.list().map((w) => ({
      workflowId: w.id,
      templateId: w.templateId,
      status: w.status,
      contextKeys: w.contextKeys,
      artifactCount: w.artifactCount,
    }));
  }

  async pause(id: string): Promise<CollaborationWorkflowSnapshot> {
    const run = this.require(id);
    if (run.status !== "Running") return this.snapshot(run);
    run.pauseRequested = true;
    run.status = "Paused";
    run.updatedAt = new Date().toISOString();
    run.resumeGate = new Promise<void>((resolve) => {
      run.resumeResolve = resolve;
    });
    this.emitTimeline(run, "workflow.paused", { message: "Paused" });
    this.emit("workflow.paused", this.snapshot(run));
    return this.snapshot(run);
  }

  async resume(id: string): Promise<CollaborationWorkflowSnapshot> {
    const run = this.require(id);
    if (run.status !== "Paused") return this.snapshot(run);
    run.pauseRequested = false;
    run.status = "Running";
    run.updatedAt = new Date().toISOString();
    run.resumeResolve?.();
    run.resumeResolve = null;
    run.resumeGate = null;
    this.emitTimeline(run, "workflow.resumed", { message: "Resumed" });
    this.emit("workflow.resumed", this.snapshot(run));
    return this.snapshot(run);
  }

  async cancel(id: string): Promise<CollaborationWorkflowSnapshot> {
    const run = this.require(id);
    if (
      run.status === "Completed" ||
      run.status === "Cancelled" ||
      run.status === "Failed"
    ) {
      return this.snapshot(run);
    }
    run.cancelRequested = true;
    run.pauseRequested = false;
    run.resumeResolve?.();
    run.status = "Cancelled";
    run.updatedAt = new Date().toISOString();
    this.emitTimeline(run, "workflow.failed", {
      error: "Cancelled",
      message: "Workflow cancelled",
    });
    this.emit("workflow.failed", this.snapshot(run));
    return this.snapshot(run);
  }

  overview() {
    const list = this.list();
    const agents = this.orchestrator.listAgents();
    const completed = list.filter((w) => w.status === "Completed").length;
    const failed = list.filter((w) => w.status === "Failed").length;
    const running = list.filter((w) => w.status === "Running").length;
    const queueSize = agents.reduce((n, a) => n + a.queueSize, 0);
    const avgResponse =
      agents.length === 0
        ? 0
        : Math.round(
            agents.reduce((n, a) => n + a.metrics.avgResponseTimeMs, 0) /
              agents.length,
          );
    const successes = agents.reduce((n, a) => n + a.metrics.successes, 0);
    const errors = agents.reduce((n, a) => n + a.metrics.errors, 0);
    const total = successes + errors;
    return {
      workflows: list.length,
      running,
      completed,
      failed,
      agents: agents.length,
      queueSize,
      avgResponseTimeMs: avgResponse,
      successRate: total === 0 ? 100 : Math.round((successes / total) * 100),
      templates: listWorkflowTemplates().length,
    };
  }

  private async executeRun(run: CollaborationRun): Promise<void> {
    const groups = groupSteps(run.template.steps);
    for (const group of groups) {
      if (run.cancelRequested) {
        run.status = "Cancelled";
        return;
      }
      await this.waitIfPaused(run);

      const parallel = group.filter((s) => !this.shouldSkip(run, s));
      for (const s of group) {
        if (!parallel.includes(s)) {
          const st = run.steps.find((x) => x.id === s.id);
          if (st) st.status = "skipped";
        }
      }
      if (!parallel.length) continue;

      run.currentStepIds = parallel.map((s) => s.id);
      run.updatedAt = new Date().toISOString();

      if (parallel.length === 1) {
        await this.runStep(run, parallel[0]!);
      } else {
        await Promise.all(parallel.map((s) => this.runStep(run, s)));
      }

      const failed = run.steps.some(
        (s) => parallel.some((p) => p.id === s.id) && s.status === "failed",
      );
      if (failed) {
        run.status = "Failed";
        run.currentStepIds = [];
        run.updatedAt = new Date().toISOString();
        this.emitTimeline(run, "workflow.failed", {
          error: "Step failed",
        });
        this.emit("workflow.failed", this.snapshot(run));
        return;
      }
    }

    if (run.cancelRequested) {
      run.status = "Cancelled";
    } else {
      run.status = "Completed";
      run.context.storeDecision("Workflow completed successfully");
      run.context.storeArtifact({
        kind: "result",
        name: "final-result",
        data: run.context.get("results") ?? run.context.entries(),
      });
      this.emitTimeline(run, "workflow.finished", {
        message: "Completed",
        result: run.context.get("results"),
      });
      this.emit("workflow.finished", this.snapshot(run));
    }
    run.currentStepIds = [];
    run.updatedAt = new Date().toISOString();
  }

  private async runStep(
    run: CollaborationRun,
    def: CollaborationStepDef,
  ): Promise<void> {
    const state = run.steps.find((s) => s.id === def.id);
    if (!state) return;

    const retries = def.retries ?? 1;
    for (let attempt = 1; attempt <= retries + 1; attempt++) {
      if (run.cancelRequested) return;
      await this.waitIfPaused(run);

      state.status = "running";
      state.attempts = attempt;
      state.startedAt = new Date().toISOString();
      this.emit("agent.busy", { agentId: def.agentId, workflowId: run.id });
      this.emitTimeline(run, "workflow.step.started", {
        stepId: def.id,
        agentId: def.agentId,
        message: `Step ${def.name}`,
      });
      this.emit("workflow.step.started", {
        workflowId: run.id,
        stepId: def.id,
        agentId: def.agentId,
      });

      try {
        const result = await this.orchestrator.runAgent(def.agentId, {
          type: def.capability ?? def.id,
          task: def.name,
          payload: {
            workflowId: run.id,
            stepId: def.id,
            goal: run.context.get("goal"),
            input: run.context.get("input"),
            priorResults: run.context.get("results"),
            context: run.context.entries(),
          },
        });

        const durationMs = result.durationMs;
        state.durationMs = durationMs;
        state.finishedAt = new Date().toISOString();

        if (!result.ok) {
          state.error = result.error ?? "Agent failed";
          if (attempt <= retries) continue;
          state.status = "failed";
          this.emit("agent.failed", { agentId: def.agentId, error: state.error });
          this.emitTimeline(run, "workflow.step.finished", {
            stepId: def.id,
            agentId: def.agentId,
            durationMs,
            error: state.error,
          });
          this.emit("agent.idle", { agentId: def.agentId });
          return;
        }

        state.status = "completed";
        state.output = result.output;
        run.context.append("results", {
          stepId: def.id,
          agentId: def.agentId,
          output: result.output,
        });
        run.context.set(`step.${def.id}`, result.output);
        run.context.storeArtifact({
          kind: "result",
          name: `${def.id}-output`,
          agentId: def.agentId,
          data: result.output,
        });
        run.context.storeLog(`Completed ${def.name}`, def.agentId);
        this.emitTimeline(run, "workflow.step.finished", {
          stepId: def.id,
          agentId: def.agentId,
          providerId: result.provider,
          durationMs,
          result: result.output,
        });
        this.emit("workflow.step.finished", {
          workflowId: run.id,
          stepId: def.id,
          agentId: def.agentId,
          ok: true,
        });
        this.emit("agent.idle", { agentId: def.agentId });
        return;
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        state.error = message;
        if (attempt <= retries) continue;
        state.status = "failed";
        state.finishedAt = new Date().toISOString();
        this.emit("agent.failed", { agentId: def.agentId, error: message });
        this.emitTimeline(run, "workflow.step.finished", {
          stepId: def.id,
          agentId: def.agentId,
          error: message,
        });
        this.emit("agent.idle", { agentId: def.agentId });
      }
    }
  }

  private shouldSkip(run: CollaborationRun, def: CollaborationStepDef): boolean {
    if (!def.when) return false;
    return run.context.get(def.when.key) !== def.when.equals;
  }

  private async waitIfPaused(run: CollaborationRun): Promise<void> {
    while (run.pauseRequested && !run.cancelRequested) {
      if (run.resumeGate) await run.resumeGate;
      else await sleep(50);
    }
  }

  private snapshot(run: CollaborationRun): CollaborationWorkflowSnapshot {
    const nodes = run.template.steps.map((s) => ({
      id: s.id,
      agentId: s.agentId,
      label: s.name,
    }));
    const edges: Array<{ from: string; to: string }> = [];
    for (let i = 0; i < run.template.steps.length - 1; i++) {
      const from = run.template.steps[i]!;
      const to = run.template.steps[i + 1]!;
      if (from.parallelGroup && from.parallelGroup === to.parallelGroup) continue;
      edges.push({ from: from.id, to: to.id });
    }
    return {
      id: run.id,
      templateId: run.template.id,
      name: run.template.name,
      status: run.status,
      priority: run.priority,
      createdAt: run.createdAt,
      updatedAt: run.updatedAt,
      estimatedMs: run.template.estimatedMs,
      elapsedMs: Date.now() - run.startedAt,
      currentStepIds: [...run.currentStepIds],
      steps: run.steps.map((s) => ({ ...s })),
      graph: { nodes, edges },
      contextKeys: run.context.keys(),
      artifactCount: run.context.listArtifacts().length,
    };
  }

  private require(id: string): CollaborationRun {
    const run = this.runs.get(id);
    if (!run) throw new Error(`Workflow not found: ${id}`);
    return run;
  }

  private emitTimeline(
    run: CollaborationRun,
    type: string,
    extra: Partial<{
      stepId: string;
      agentId: string;
      providerId: string;
      durationMs: number;
      result: unknown;
      error: string;
      message: string;
    }>,
  ): void {
    this.timeline.push({
      type,
      workflowId: run.id,
      ...extra,
    });
  }

  private emit(type: string, payload: unknown): void {
    for (const listener of this.listeners) {
      try {
        listener({ type, payload });
      } catch {
        /* ignore */
      }
    }
  }

  private nextId(): string {
    this.seq += 1;
    return `cwf_${Date.now().toString(36)}_${this.seq}`;
  }
}

function groupSteps(
  steps: readonly CollaborationStepDef[],
): CollaborationStepDef[][] {
  const groups: CollaborationStepDef[][] = [];
  let i = 0;
  while (i < steps.length) {
    const step = steps[i]!;
    if (step.parallelGroup || step.mode === "parallel") {
      const key = step.parallelGroup ?? step.id;
      const group = [step];
      i += 1;
      while (i < steps.length) {
        const next = steps[i]!;
        if (
          next.parallelGroup === key ||
          (next.mode === "parallel" && next.parallelGroup === key)
        ) {
          group.push(next);
          i += 1;
        } else break;
      }
      groups.push(group);
    } else {
      groups.push([step]);
      i += 1;
    }
  }
  return groups;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function createCollaborationEngine(
  orchestrator: AiOrchestrator,
): CollaborationEngine {
  return new CollaborationEngine(orchestrator);
}
