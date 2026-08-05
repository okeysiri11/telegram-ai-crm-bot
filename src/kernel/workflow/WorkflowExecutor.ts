import type { IWorkflowExecutor } from "./interfaces.js";
import type { StepHandler } from "./interfaces.js";
import type { WorkflowEngineOptions } from "./types.js";
import type { WorkflowHistory } from "./WorkflowHistory.js";
import type { WorkflowInstance } from "./WorkflowInstance.js";
import type { WorkflowScheduler } from "./WorkflowScheduler.js";
import type { WorkflowStep } from "./WorkflowStep.js";

export interface ExecutorDeps {
  readonly history: WorkflowHistory;
  readonly scheduler: WorkflowScheduler;
  readonly handlers: Map<string, StepHandler>;
  readonly options: WorkflowEngineOptions;
  readonly onWaiting?: (instance: WorkflowInstance) => void;
}

/**
 * Executes workflow steps: sequential, parallel, condition, approval, retry, compensate.
 */
export class WorkflowExecutor implements IWorkflowExecutor {
  constructor(private readonly deps: ExecutorDeps) {}

  async run(instance: WorkflowInstance): Promise<WorkflowInstance> {
    instance.state.assert("Created", "Running", "Suspended");
    if (instance.status === "Created" || instance.status === "Suspended") {
      instance.state.transition("Running");
    }
    if (instance.activeSteps.length === 0) {
      instance.activeSteps = [instance.definition.start];
    }
    this.log(instance, "WorkflowStarted", undefined, {
      start: instance.definition.start,
    });
    await this.publishBus("WorkflowStarted", {
      instanceId: instance.id,
      definitionId: instance.definitionId,
    });
    return this.pump(instance);
  }

  async resume(instance: WorkflowInstance): Promise<WorkflowInstance> {
    if (
      instance.status === "WaitingApproval" ||
      instance.status === "WaitingEvent" ||
      instance.status === "Suspended"
    ) {
      instance.state.transition("Running");
    }
    instance.state.assert("Running", "Compensating");
    return this.pump(instance);
  }

  private async pump(instance: WorkflowInstance): Promise<WorkflowInstance> {
    let guard = 0;
    for (;;) {
      const status = instance.state.status;
      if (status !== "Running" && status !== "Compensating") {
        break;
      }
      guard += 1;
      if (guard > 10_000) {
        instance.lastError = "Workflow execution exceeded step guard limit";
        instance.state.transition("Failed");
        this.log(instance, "WorkflowFailed", undefined, {
          error: instance.lastError,
        });
        break;
      }

      if (status === "Compensating") {
        await this.runCompensation(instance);
        continue;
      }

      if (instance.activeSteps.length === 0) {
        instance.state.transition("Completed");
        instance.touch();
        this.log(instance, "WorkflowFinished");
        await this.publishBus("WorkflowFinished", {
          instanceId: instance.id,
          definitionId: instance.definitionId,
          status: "Completed",
        });
        break;
      }

      if (instance.activeSteps.length > 1) {
        await this.executeParallelActive(instance);
        const afterParallel = instance.state.status;
        if (
          afterParallel === "WaitingApproval" ||
          afterParallel === "WaitingEvent" ||
          afterParallel === "Failed"
        ) {
          break;
        }
        continue;
      }

      const stepId = instance.activeSteps[0];
      if (!stepId) break;
      const step = instance.definition.getStep(stepId);
      if (!step) {
        instance.lastError = `Unknown step: ${stepId}`;
        instance.state.transition("Failed");
        this.log(instance, "WorkflowFailed", stepId, {
          error: instance.lastError,
        });
        break;
      }

      const cont = await this.executeStep(instance, step);
      if (!cont) {
        continue;
      }
    }
    instance.touch();
    return instance;
  }

  private async executeParallelActive(
    instance: WorkflowInstance,
  ): Promise<void> {
    const ids = [...instance.activeSteps];
    const results = await Promise.all(
      ids.map(async (id) => {
        const step = instance.definition.getStep(id);
        if (!step) return { id, ok: false as const, error: "missing" };
        try {
          await this.runTaskBody(instance, step);
          return { id, ok: true as const };
        } catch (e) {
          return {
            id,
            ok: false as const,
            error: e instanceof Error ? e.message : String(e),
          };
        }
      }),
    );

    const failed = results.filter((r) => !r.ok);
    if (failed.length > 0) {
      instance.lastError = failed.map((f) => `${f.id}: ${f.error}`).join("; ");
      await this.failOrCompensate(instance, ids[0]!);
      return;
    }

    // All branch tasks done — collect next from each and unique join targets
    const nextSet = new Set<string>();
    for (const id of ids) {
      const step = instance.definition.getStep(id)!;
      instance.completedSteps.push(id);
      if (step.compensateWith) instance.compensationStack.push(id);
      for (const n of step.next) nextSet.add(n);
      const st = instance.ensureStepState(id);
      st.status = "completed";
    }
    instance.activeSteps = [...nextSet];
  }

  private async executeStep(
    instance: WorkflowInstance,
    step: WorkflowStep,
  ): Promise<boolean> {
    this.log(instance, "StepStarted", step.id, { kind: step.kind });

    switch (step.kind) {
      case "parallel": {
        instance.completedSteps.push(step.id);
        instance.activeSteps = [...step.next];
        this.log(instance, "ParallelFork", step.id, {
          branches: step.next,
        });
        return true;
      }
      case "condition": {
        const ok = step.condition?.(instance.context) === true;
        const next = ok ? step.whenTrue : step.whenFalse;
        instance.completedSteps.push(step.id);
        instance.activeSteps = next ? [next] : [];
        this.log(instance, "ConditionEvaluated", step.id, { ok, next });
        return true;
      }
      case "approval": {
        instance.waitingApprovalStepId = step.id;
        instance.state.transition("WaitingApproval");
        this.log(instance, "ApprovalRequested", step.id, {
          role: step.approvalRole,
        });
        this.deps.onWaiting?.(instance);
        return false;
      }
      case "event-wait": {
        instance.waitingEventType = step.waitEventType ?? null;
        instance.state.transition("WaitingEvent");
        this.log(instance, "EventWait", step.id, {
          eventType: step.waitEventType,
        });
        this.deps.onWaiting?.(instance);
        return false;
      }
      case "delay": {
        const ms = step.timeout?.ms ?? 0;
        const jobId = `${instance.id}:${step.id}:delay`;
        instance.state.transition("Suspended");
        this.deps.scheduler.schedule(jobId, ms, () => {
          instance.completedSteps.push(step.id);
          instance.activeSteps = [...step.next];
          instance.state.transition("Running");
          void this.resume(instance);
        });
        this.log(instance, "DelayScheduled", step.id, { ms });
        return false;
      }
      case "compensation": {
        await this.runTaskBody(instance, step);
        instance.completedSteps.push(step.id);
        instance.activeSteps = [...step.next];
        return true;
      }
      case "task":
      default: {
        try {
          await this.runTaskBody(instance, step);
          instance.completedSteps.push(step.id);
          if (step.compensateWith) {
            instance.compensationStack.push(step.id);
          }
          instance.activeSteps = [...step.next];
          this.log(instance, "StepCompleted", step.id);
          return true;
        } catch (err) {
          const message = err instanceof Error ? err.message : String(err);
          instance.lastError = message;
          this.log(instance, "StepFailed", step.id, { error: message });
          await this.failOrCompensate(instance, step.id);
          return false;
        }
      }
    }
  }

  private async runTaskBody(
    instance: WorkflowInstance,
    step: WorkflowStep,
  ): Promise<void> {
    const st = instance.ensureStepState(step.id);
    const retry = step.retry ?? this.deps.options.defaultRetry;
    const maxAttempts = retry?.maxAttempts ?? 1;
    const backoff = retry?.backoffMs ?? 0;
    const mult = retry?.backoffMultiplier ?? 1;

    let lastError: unknown;
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      st.attempts = attempt;
      st.status = "running";
      try {
        const output = await this.invokeWithTimeout(instance, step);
        st.output = output;
        st.status = "completed";
        instance.context.set(`step.${step.id}.output`, output);
        return;
      } catch (err) {
        lastError = err;
        st.status = "failed";
        st.error = err instanceof Error ? err.message : String(err);
        if (attempt < maxAttempts && backoff > 0) {
          const wait = backoff * Math.pow(mult, attempt - 1);
          await sleep(wait);
        }
      }
    }
    throw lastError instanceof Error
      ? lastError
      : new Error(String(lastError));
  }

  private async invokeWithTimeout(
    instance: WorkflowInstance,
    step: WorkflowStep,
  ): Promise<unknown> {
    const work = this.invoke(instance, step);
    if (!step.timeout?.ms) return work;
    return Promise.race([
      work,
      new Promise<never>((_, reject) => {
        setTimeout(
          () => reject(new Error(`Step ${step.id} timed out`)),
          step.timeout!.ms,
        );
      }),
    ]);
  }

  private async invoke(
    instance: WorkflowInstance,
    step: WorkflowStep,
  ): Promise<unknown> {
    if (step.handlerId) {
      const handler = this.deps.handlers.get(step.handlerId);
      if (!handler) {
        throw new Error(`Handler not registered: ${step.handlerId}`);
      }
      return handler(instance.context, instance.context.entries());
    }
    if (step.capability) {
      const mesh = this.deps.options.serviceMesh;
      if (!mesh) {
        throw new Error(
          `Step ${step.id} requires service mesh for capability ${step.capability}`,
        );
      }
      const result = await mesh.route({
        capability: step.capability,
        method: step.method,
        input: instance.context.entries(),
      });
      if (!result.ok) {
        throw new Error(result.error ?? "Mesh route failed");
      }
      return result.data;
    }
    // No-op task (structural)
    return null;
  }

  private async failOrCompensate(
    instance: WorkflowInstance,
    stepId: string,
  ): Promise<void> {
    const step = instance.definition.getStep(stepId);
    if (step?.onError) {
      instance.activeSteps = [step.onError];
      instance.state.transition("Running");
      return;
    }
    if (instance.compensationStack.length > 0) {
      instance.state.transition("Compensating");
      return;
    }
    instance.state.transition("Failed");
    this.log(instance, "WorkflowFailed", stepId, {
      error: instance.lastError,
    });
    await this.publishBus("WorkflowFinished", {
      instanceId: instance.id,
      status: "Failed",
      error: instance.lastError,
    });
  }

  private async runCompensation(instance: WorkflowInstance): Promise<void> {
    const originId = instance.compensationStack.pop();
    if (!originId) {
      instance.state.transition("Compensated");
      this.log(instance, "WorkflowCompensated");
      instance.activeSteps = [];
      return;
    }
    const origin = instance.definition.getStep(originId);
    const compId = origin?.compensateWith;
    if (!compId) {
      return;
    }
    const comp = instance.definition.getStep(compId);
    if (!comp) {
      instance.lastError = `Missing compensation step ${compId}`;
      instance.state.transition("Failed");
      return;
    }
    try {
      await this.runTaskBody(instance, comp);
      this.log(instance, "CompensationCompleted", compId, {
        forStep: originId,
      });
    } catch (err) {
      instance.lastError =
        err instanceof Error ? err.message : String(err);
      instance.state.transition("Failed");
      this.log(instance, "CompensationFailed", compId, {
        error: instance.lastError,
      });
    }
  }

  private log(
    instance: WorkflowInstance,
    type: string,
    stepId?: string,
    data?: unknown,
  ): void {
    this.deps.history.append({
      instanceId: instance.id,
      type,
      ...(stepId !== undefined ? { stepId } : {}),
      ...(data !== undefined ? { data } : {}),
    });
  }

  private async publishBus(type: string, payload: unknown): Promise<void> {
    const bus = this.deps.options.eventBus;
    if (!bus) return;
    await bus.publish({ type, payload, mode: "async" });
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
