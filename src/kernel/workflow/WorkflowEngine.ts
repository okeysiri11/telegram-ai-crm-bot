import type { IWorkflowEngine } from "./interfaces.js";
import type { StepHandler } from "./interfaces.js";
import type {
  ApprovalDecision,
  StartWorkflowOptions,
  WorkflowDefinitionInit,
  WorkflowEngineOptions,
  WorkflowHistoryEntry,
  WorkflowInstanceStatus,
} from "./types.js";
import { WorkflowDefinition } from "./WorkflowDefinition.js";
import { WorkflowExecutor } from "./WorkflowExecutor.js";
import { WorkflowHistory } from "./WorkflowHistory.js";
import { WorkflowInstance } from "./WorkflowInstance.js";
import { WorkflowScheduler } from "./WorkflowScheduler.js";
import { WorkflowValidator } from "./WorkflowValidator.js";

let instanceSeq = 0;

/**
 * ADOS Enterprise Workflow Engine.
 *
 * Kernel → Event Bus → Service Mesh → Workflow Engine → Runtime → Agents → Modules
 *
 * Communicates only through Event Bus and Service Mesh (DI). No business imports.
 */
export class WorkflowEngine implements IWorkflowEngine {
  private readonly definitions = new Map<string, WorkflowDefinition>();
  private readonly instances = new Map<string, WorkflowInstance>();
  private readonly handlers = new Map<string, StepHandler>();
  private readonly historyStore = new WorkflowHistory();
  private readonly scheduler = new WorkflowScheduler();
  private readonly validator = new WorkflowValidator();
  private readonly executor: WorkflowExecutor;
  private readonly options: WorkflowEngineOptions;
  private readonly unsubscribers: Array<() => void> = [];

  constructor(options?: WorkflowEngineOptions) {
    this.options = options ?? {};
    this.executor = new WorkflowExecutor({
      history: this.historyStore,
      scheduler: this.scheduler,
      handlers: this.handlers,
      options: this.options,
    });

    // Event-driven resume for event-wait steps
    if (this.options.eventBus) {
      const sub = this.options.eventBus.subscribe("*", (event) => {
        for (const instance of this.instances.values()) {
          if (
            instance.status === "WaitingEvent" &&
            instance.waitingEventType &&
            (event.type === instance.waitingEventType ||
              instance.waitingEventType === "*")
          ) {
            const stepId = instance.activeSteps[0];
            instance.context.set("lastEvent", event.payload);
            instance.waitingEventType = null;
            if (stepId) {
              const step = instance.definition.getStep(stepId);
              instance.completedSteps.push(stepId);
              instance.activeSteps = step ? [...step.next] : [];
            }
            void this.executor.resume(instance);
          }
        }
      });
      this.unsubscribers.push(() => sub.unsubscribe());
    }
  }

  register(
    definition: WorkflowDefinition | WorkflowDefinitionInit,
  ): WorkflowDefinition {
    const def =
      definition instanceof WorkflowDefinition
        ? definition
        : WorkflowDefinition.create(definition);
    this.validator.assertValid(def);
    this.definitions.set(def.id, def);
    return def;
  }

  unregister(definitionId: string): boolean {
    return this.definitions.delete(definitionId);
  }

  getDefinition(definitionId: string): WorkflowDefinition | undefined {
    return this.definitions.get(definitionId);
  }

  listDefinitions(): readonly WorkflowDefinition[] {
    return Object.freeze([...this.definitions.values()]);
  }

  registerHandler(handlerId: string, handler: StepHandler): void {
    this.handlers.set(handlerId, handler);
  }

  async start(
    definitionId: string,
    options?: StartWorkflowOptions,
  ): Promise<WorkflowInstance> {
    const def = this.definitions.get(definitionId);
    if (!def) {
      throw new Error(`Workflow definition not found: ${definitionId}`);
    }
    instanceSeq += 1;
    const id = options?.instanceId ?? `wf_${instanceSeq}_${Date.now().toString(36)}`;
    const instance = new WorkflowInstance(id, def, options?.input);
    this.instances.set(id, instance);
    return this.executor.run(instance);
  }

  async approve(
    instanceId: string,
    stepId: string,
    decision: ApprovalDecision,
  ): Promise<WorkflowInstance> {
    const instance = this.requireInstance(instanceId);
    instance.state.assert("WaitingApproval");
    if (instance.waitingApprovalStepId !== stepId) {
      throw new Error(
        `Not waiting for approval on step ${stepId} (waiting ${instance.waitingApprovalStepId})`,
      );
    }
    this.historyStore.append({
      instanceId,
      type: decision.approved ? "ApprovalGranted" : "ApprovalRejected",
      stepId,
      data: decision,
    });
    instance.waitingApprovalStepId = null;
    const step = instance.definition.getStep(stepId);
    if (!decision.approved) {
      instance.lastError = decision.comment ?? "Approval rejected";
      if (instance.compensationStack.length > 0) {
        instance.state.transition("Compensating");
        return this.executor.resume(instance);
      }
      instance.state.transition("Failed");
      return instance;
    }
    instance.completedSteps.push(stepId);
    instance.activeSteps = step ? [...step.next] : [];
    instance.context.set(`approval.${stepId}`, decision);
    return this.executor.resume(instance);
  }

  async resume(instanceId: string): Promise<WorkflowInstance> {
    const instance = this.requireInstance(instanceId);
    return this.executor.resume(instance);
  }

  /** Soft-pause: Running / waiting → Suspended (resume restores). */
  async pause(instanceId: string, reason?: string): Promise<WorkflowInstance> {
    const instance = this.requireInstance(instanceId);
    if (instance.status === "Suspended") return instance;
    if (!instance.state.canTransition("Suspended")) {
      throw new Error(`Cannot pause workflow in status ${instance.status}`);
    }
    this.scheduler.cancel(`${instanceId}:*`);
    instance.lastError = reason ?? "Paused from Control Center";
    instance.state.transition("Suspended");
    instance.touch();
    this.historyStore.append({
      instanceId,
      type: "WorkflowSuspended",
      ...(reason !== undefined ? { message: reason } : {}),
    });
    return instance;
  }

  async cancel(
    instanceId: string,
    reason?: string,
  ): Promise<WorkflowInstance> {
    const instance = this.requireInstance(instanceId);
    if (
      instance.status === "Completed" ||
      instance.status === "Cancelled" ||
      instance.status === "Compensated"
    ) {
      return instance;
    }
    this.scheduler.cancel(`${instanceId}:*`);
    instance.lastError = reason ?? "Cancelled";
    instance.state.transition("Cancelled");
    instance.activeSteps = [];
    instance.touch();
    this.historyStore.append({
      instanceId,
      type: "WorkflowCancelled",
      ...(reason !== undefined ? { message: reason } : {}),
    });
    return instance;
  }

  getInstance(instanceId: string): WorkflowInstance | undefined {
    return this.instances.get(instanceId);
  }

  listInstances(
    status?: WorkflowInstanceStatus,
  ): readonly WorkflowInstance[] {
    const all = [...this.instances.values()];
    if (!status) return Object.freeze(all);
    return Object.freeze(all.filter((i) => i.status === status));
  }

  history(instanceId: string): readonly WorkflowHistoryEntry[] {
    return this.historyStore.list(instanceId);
  }

  /** Persistence snapshot for resume-after-interruption tooling. */
  persistHistory(): readonly WorkflowHistoryEntry[] {
    return this.historyStore.persistAll();
  }

  dispose(): void {
    for (const u of this.unsubscribers) u();
    this.unsubscribers.length = 0;
    this.scheduler.clear();
    this.instances.clear();
    this.definitions.clear();
    this.handlers.clear();
    this.historyStore.clear();
  }

  private requireInstance(id: string): WorkflowInstance {
    const instance = this.instances.get(id);
    if (!instance) throw new Error(`Workflow instance not found: ${id}`);
    return instance;
  }
}

export function createWorkflowEngine(
  options?: WorkflowEngineOptions,
): WorkflowEngine {
  return new WorkflowEngine(options);
}

/**
 * Example enterprise delivery pipeline (agents as handler ids — no module imports).
 */
export function createEnterpriseDeliveryWorkflow(): WorkflowDefinitionInit {
  return {
    id: "enterprise.delivery",
    name: "Enterprise Feature Delivery",
    version: "1.0.0",
    start: "architect",
    steps: [
      {
        id: "architect",
        name: "Enterprise Architect",
        kind: "task",
        handlerId: "agent.architect",
        next: ["backend"],
        compensateWith: "compensate.architect",
      },
      {
        id: "backend",
        name: "Backend Engineer",
        kind: "task",
        handlerId: "agent.backend",
        next: ["parallel.dev"],
        retry: { maxAttempts: 2, backoffMs: 1 },
      },
      {
        id: "parallel.dev",
        name: "Database ∥ Frontend",
        kind: "parallel",
        next: ["database", "frontend"],
      },
      {
        id: "database",
        name: "Database Engineer",
        kind: "task",
        handlerId: "agent.database",
        next: ["qa"],
      },
      {
        id: "frontend",
        name: "Frontend Engineer",
        kind: "task",
        handlerId: "agent.frontend",
        next: ["qa"],
      },
      {
        id: "qa",
        name: "QA Engineer",
        kind: "task",
        handlerId: "agent.qa",
        next: ["docs"],
      },
      {
        id: "docs",
        name: "Documentation Engineer",
        kind: "task",
        handlerId: "agent.docs",
        next: ["knowledge"],
      },
      {
        id: "knowledge",
        name: "Knowledge Engineer",
        kind: "task",
        handlerId: "agent.knowledge",
        next: ["approval.release"],
      },
      {
        id: "approval.release",
        name: "Release Approval",
        kind: "approval",
        approvalRole: "CEO",
        next: ["devops"],
      },
      {
        id: "devops",
        name: "DevOps",
        kind: "task",
        handlerId: "agent.devops",
        next: ["release"],
      },
      {
        id: "release",
        name: "Release",
        kind: "task",
        handlerId: "agent.release",
        next: [],
      },
      {
        id: "compensate.architect",
        name: "Compensate Architect",
        kind: "compensation",
        handlerId: "agent.architect.compensate",
        next: [],
      },
    ],
  };
}
