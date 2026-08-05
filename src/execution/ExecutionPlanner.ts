import type { AiOrchestrator } from "@ados/orchestrator";
import {
  ExecutionPlan,
  createExecutionPlan,
} from "./ExecutionPlan.js";
import { TaskAnalyzer, createTaskAnalyzer } from "./TaskAnalyzer.js";
import { TaskSplitter, createTaskSplitter } from "./TaskSplitter.js";
import {
  DependencyResolver,
  createDependencyResolver,
} from "./DependencyResolver.js";
import { ExecutionQueue, createExecutionQueue } from "./ExecutionQueue.js";
import {
  ExecutionMonitor,
  createExecutionMonitor,
} from "./ExecutionMonitor.js";
import {
  ExecutionScheduler,
  createExecutionScheduler,
} from "./ExecutionScheduler.js";
import {
  ExecutionReporter,
  createExecutionReporter,
} from "./ExecutionReporter.js";
import {
  ExecutionValidator,
  createExecutionValidator,
} from "./ExecutionValidator.js";
import {
  ExecutionHistory,
  createExecutionHistory,
} from "./ExecutionHistory.js";
import type {
  EngineeringSpecification,
  ExecutionEvent,
  ExecutionReport,
} from "./types.js";
import type { ExecutionEventListener } from "./ExecutionPlan.js";

export interface ExecutionPlannerOptions {
  readonly orchestrator: AiOrchestrator;
  readonly autoRun?: boolean;
}

/**
 * Enterprise Execution Planner — ChatGPT specs → Orchestrator work packages.
 * Never invents architecture; only executes the given specification.
 */
export class ExecutionPlanner {
  readonly analyzer: TaskAnalyzer;
  readonly splitter: TaskSplitter;
  readonly resolver: DependencyResolver;
  readonly queue: ExecutionQueue;
  readonly monitor: ExecutionMonitor;
  readonly validator: ExecutionValidator;
  readonly reporter: ExecutionReporter;
  readonly history: ExecutionHistory;
  readonly scheduler: ExecutionScheduler;

  private current: ExecutionPlan | null = null;
  private lastReport: ExecutionReport | null = null;
  private readonly listeners = new Set<ExecutionEventListener>();
  private readonly autoRun: boolean;

  constructor(options: ExecutionPlannerOptions) {
    this.autoRun = options.autoRun ?? true;
    this.analyzer = createTaskAnalyzer();
    this.splitter = createTaskSplitter();
    this.resolver = createDependencyResolver();
    this.queue = createExecutionQueue();
    this.monitor = createExecutionMonitor();
    this.validator = createExecutionValidator();
    this.reporter = createExecutionReporter(this.validator);
    this.history = createExecutionHistory();
    this.scheduler = createExecutionScheduler(
      options.orchestrator,
      this.resolver,
      this.queue,
      this.validator,
    );
  }

  on(listener: ExecutionEventListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Accept engineering specification, build plan, optionally execute.
   */
  async plan(
    input: EngineeringSpecification | string | Record<string, unknown>,
    options?: { autoRun?: boolean },
  ): Promise<{
    plan: ReturnType<ExecutionPlan["snapshot"]>;
    analysis: ReturnType<DependencyResolver["analyze"]>;
    report: ExecutionReport | null;
  }> {
    const analyzed = this.analyzer.analyze(input);
    const plan = createExecutionPlan(analyzed.specification);
    this.splitter.split(plan, analyzed);
    const analysis = this.resolver.analyze(plan);

    this.current = plan;
    this.wirePlanEvents(plan);
    plan.emit("plan.created", plan.snapshot());
    this.fanout({ type: "plan.created", at: new Date().toISOString(), payload: plan.snapshot() });

    const shouldRun = options?.autoRun ?? this.autoRun;
    let report: ExecutionReport | null = null;
    if (shouldRun) {
      await this.scheduler.runPlan(plan);
      report = this.reporter.report(plan);
      this.lastReport = report;
      this.history.push({
        planId: plan.id,
        status: plan.status,
        progress: plan.snapshot().progress,
        report,
        snapshot: plan.snapshot(),
      });
    }

    return {
      plan: plan.snapshot(),
      analysis,
      report,
    };
  }

  /** Execute current draft/ready plan if not already running. */
  async run(planId?: string): Promise<ExecutionReport> {
    const plan = this.requirePlan(planId);
    if (plan.status === "running") {
      throw new Error("Plan already running");
    }
    await this.scheduler.runPlan(plan);
    const report = this.reporter.report(plan);
    this.lastReport = report;
    this.history.push({
      planId: plan.id,
      status: plan.status,
      progress: plan.snapshot().progress,
      report,
      snapshot: plan.snapshot(),
    });
    return report;
  }

  status(planId?: string) {
    const plan = planId ? this.requirePlan(planId) : this.current;
    const snap = this.monitor.snapshot(plan);
    const analysis = plan ? this.resolver.analyze(plan) : null;
    return {
      id: "ados.execution",
      name: "Enterprise Execution Planner",
      health: "OK" as const,
      currentPlan: snap,
      analysis,
      queue: this.queue.snapshot(),
      runningAgents: snap?.runningAgents ?? [],
      completedTasks: plan ? this.monitor.completedTasks(plan).map((t) => t.id) : [],
      blockedTasks: plan ? this.monitor.blockedTasks(plan).map((t) => t.id) : [],
      failedTasks: plan ? this.monitor.failedTasks(plan).map((t) => t.id) : [],
      logs: plan ? this.monitor.logs(plan) : [],
      lastReport: this.lastReport,
    };
  }

  getReport(planId?: string): ExecutionReport | null {
    if (planId) {
      const hist = this.history.getByPlanId(planId);
      if (hist?.report) return hist.report;
      if (this.current?.id === planId) {
        return this.reporter.report(this.current);
      }
      return null;
    }
    if (this.lastReport) return this.lastReport;
    if (this.current && this.current.status !== "draft" && this.current.status !== "ready") {
      return this.reporter.report(this.current);
    }
    return null;
  }

  listHistory(limit = 50) {
    return this.history.list(limit);
  }

  getCurrentPlan(): ExecutionPlan | null {
    return this.current;
  }

  private requirePlan(planId?: string): ExecutionPlan {
    if (!this.current) throw new Error("No active execution plan");
    if (planId && this.current.id !== planId) {
      throw new Error(`Plan not found or not active: ${planId}`);
    }
    return this.current;
  }

  private wirePlanEvents(plan: ExecutionPlan): void {
    plan.on((event) => this.fanout(event));
  }

  private fanout(event: ExecutionEvent): void {
    for (const l of this.listeners) {
      try {
        l(event);
      } catch {
        /* ignore */
      }
    }
  }
}

export function createExecutionPlanner(
  options: ExecutionPlannerOptions,
): ExecutionPlanner {
  return new ExecutionPlanner(options);
}
