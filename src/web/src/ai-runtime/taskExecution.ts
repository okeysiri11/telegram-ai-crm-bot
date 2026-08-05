/**
 * Sprint 30.5 — AI Task Execution facade over Job Manager.
 * Create · Start · Pause · Resume · Cancel · Retry · History · Logs
 */

import { jobManager } from "@/enterprise-runtime/jobManager";
import type {
  AiTaskStage,
  JobLifecycle,
  JobPriority,
  RuntimeJobLog,
  RuntimeJobRecord,
} from "@/enterprise-runtime/types";
import { stageFromLifecycle } from "./taskPipeline";
import {
  auditAiTask,
  canAccessTaskResource,
  canManageAiTasks,
  type AiTaskSecurityContext,
} from "./aiTaskSecurity";
import { enforcePromptSecurity } from "./aiPromptSecurity";

export type CreateAiTaskInput = {
  title: string;
  agentId?: string;
  studioId?: string;
  priority?: JobPriority;
  source?: RuntimeJobRecord["source"];
};

function now() {
  return new Date().toISOString();
}

function appendLog(job: RuntimeJobRecord, message: string, level: RuntimeJobLog["level"] = "info"): RuntimeJobRecord {
  const entry: RuntimeJobLog = { at: now(), message, level };
  return {
    ...job,
    logs: [...(job.logs || []), entry].slice(-40),
    history: [...(job.history || []), entry].slice(-80),
    updatedAt: now(),
  };
}

function requireManage(ctx: AiTaskSecurityContext) {
  if (!canManageAiTasks(ctx)) {
    throw new Error("Недостаточно прав для управления AI-задачами");
  }
}

function requireAccess(ctx: AiTaskSecurityContext, job: RuntimeJobRecord) {
  if (!canAccessTaskResource(ctx, { orgId: job.orgId, workspaceId: job.workspaceId })) {
    throw new Error("Задача недоступна в этом workspace / организации");
  }
}

export const taskExecution = {
  list(ctx: AiTaskSecurityContext): RuntimeJobRecord[] {
    if (!canManageAiTasks(ctx) && !canAccessTaskResource(ctx, { orgId: ctx.orgId, workspaceId: ctx.workspaceId })) {
      return [];
    }
    return jobManager
      .list()
      .filter((j) => canAccessTaskResource(ctx, { orgId: j.orgId || ctx.orgId, workspaceId: j.workspaceId || ctx.workspaceId }))
      .map((j) => ({
        ...j,
        stage: j.stage || stageFromLifecycle(j.status, j.progress),
      }));
  },

  get(ctx: AiTaskSecurityContext, id: string): RuntimeJobRecord | undefined {
    const job = jobManager.list().find((j) => j.id === id);
    if (!job) return undefined;
    requireAccess(ctx, { ...job, orgId: job.orgId || ctx.orgId, workspaceId: job.workspaceId || ctx.workspaceId });
    return { ...job, stage: job.stage || stageFromLifecycle(job.status, job.progress) };
  },

  async create(ctx: AiTaskSecurityContext, input: CreateAiTaskInput): Promise<RuntimeJobRecord> {
    requireManage(ctx);
    const guarded = await enforcePromptSecurity(input.title, {
      actor: ctx.actor,
      orgId: ctx.orgId,
      workspaceId: ctx.workspaceId,
      maxTokens: 2048,
    });
    const title = guarded.sanitized;
    const id = `ai_task_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
    const t = now();
    let job: RuntimeJobRecord = {
      id,
      title,
      status: "waiting",
      progress: 0,
      etaSec: 120,
      source: input.source || "ai",
      startedAt: t,
      updatedAt: t,
      retries: 0,
      priority: input.priority || "normal",
      stage: "waiting",
      orgId: ctx.orgId,
      workspaceId: ctx.workspaceId,
      agentId: input.agentId,
      agentIds: input.agentId ? [input.agentId] : undefined,
      studioId: input.studioId,
      queueKind: "task",
      logs: [],
      history: [],
    };
    job = appendLog(job, `Создана задача · ${title}`);
    jobManager.upsert(job);
    await auditAiTask(ctx, "create", id, title);
    return job;
  },

  async start(ctx: AiTaskSecurityContext, id: string): Promise<RuntimeJobRecord | undefined> {
    requireManage(ctx);
    const cur = this.get(ctx, id);
    if (!cur) return undefined;
    let job = appendLog(cur, "Старт выполнения");
    job = {
      ...job,
      status: "running",
      stage: "preparing" as AiTaskStage,
      progress: Math.max(5, job.progress),
      updatedAt: now(),
    };
    jobManager.upsert(job);
    await auditAiTask(ctx, "start", id);
    return job;
  },

  async pause(ctx: AiTaskSecurityContext, id: string): Promise<RuntimeJobRecord | undefined> {
    requireManage(ctx);
    const cur = this.get(ctx, id);
    if (!cur) return undefined;
    let job = appendLog(cur, "Пауза", "warn");
    job = { ...job, status: "paused", stage: "preparing", updatedAt: now() };
    jobManager.upsert(job);
    await auditAiTask(ctx, "pause", id);
    return job;
  },

  async resume(ctx: AiTaskSecurityContext, id: string): Promise<RuntimeJobRecord | undefined> {
    requireManage(ctx);
    const cur = this.get(ctx, id);
    if (!cur) return undefined;
    let job = appendLog(cur, "Возобновление");
    job = { ...job, status: "running", stage: "running", updatedAt: now() };
    jobManager.upsert(job);
    await auditAiTask(ctx, "resume", id);
    return job;
  },

  async cancel(ctx: AiTaskSecurityContext, id: string): Promise<RuntimeJobRecord | undefined> {
    requireManage(ctx);
    const cur = this.get(ctx, id);
    if (!cur) return undefined;
    let job = appendLog(cur, "Отмена", "warn");
    job = { ...job, status: "cancelled", stage: "completed", progress: 100, etaSec: 0, updatedAt: now() };
    jobManager.upsert(job);
    await auditAiTask(ctx, "cancel", id);
    return job;
  },

  async retry(ctx: AiTaskSecurityContext, id: string): Promise<RuntimeJobRecord | undefined> {
    requireManage(ctx);
    const cur = this.get(ctx, id);
    if (!cur) return undefined;
    let job = appendLog(cur, `Повтор · попытка ${cur.retries + 1}`);
    job = {
      ...job,
      status: "retrying",
      stage: "waiting",
      progress: Math.max(5, cur.progress - 10),
      retries: cur.retries + 1,
      etaSec: 120,
      updatedAt: now(),
    };
    jobManager.upsert(job);
    await auditAiTask(ctx, "retry", id);
    return job;
  },

  async setPriority(ctx: AiTaskSecurityContext, id: string, priority: JobPriority): Promise<RuntimeJobRecord | undefined> {
    requireManage(ctx);
    const cur = this.get(ctx, id);
    if (!cur) return undefined;
    let job = appendLog(cur, `Приоритет → ${priority}`);
    job = { ...job, priority, updatedAt: now() };
    jobManager.upsert(job);
    await auditAiTask(ctx, "priority", id, priority);
    return job;
  },

  /** Owner force-stop — cancel + audit. */
  async forceStop(ctx: AiTaskSecurityContext, id: string): Promise<RuntimeJobRecord | undefined> {
    requireManage(ctx);
    const cur = this.get(ctx, id);
    if (!cur) return undefined;
    let job = appendLog(cur, "Принудительная остановка (Owner)", "error");
    job = { ...job, status: "cancelled", stage: "failed", progress: 100, etaSec: 0, updatedAt: now() };
    jobManager.upsert(job);
    await auditAiTask(ctx, "force_stop", id);
    return job;
  },

  logs(ctx: AiTaskSecurityContext, id: string): RuntimeJobLog[] {
    return this.get(ctx, id)?.logs || [];
  },

  history(ctx: AiTaskSecurityContext, id: string): RuntimeJobLog[] {
    return this.get(ctx, id)?.history || [];
  },

  dashboard(ctx: AiTaskSecurityContext) {
    const jobs = this.list(ctx);
    const active = jobs.filter((j) => j.status === "running" || j.status === "paused" || j.status === "retrying");
    const completed = jobs.filter((j) => j.status === "completed");
    const failed = jobs.filter((j) => j.status === "failed");
    const queue = jobs.filter((j) => j.status === "waiting" || j.status === "retrying");
    const runtimes = completed
      .map((j) => Math.max(1, new Date(j.updatedAt).getTime() - new Date(j.startedAt).getTime()) / 1000)
      .filter((n) => Number.isFinite(n));
    const avgRuntimeSec = runtimes.length
      ? Math.round(runtimes.reduce((a, b) => a + b, 0) / runtimes.length)
      : 0;
    const settled = completed.length + failed.length;
    const successRate = settled ? Math.round((completed.length / settled) * 100) : 100;
    return {
      activeAgents: new Set(active.map((j) => j.agentId).filter(Boolean)).size,
      activeTasks: active.length,
      completedTasks: completed.length,
      queueLength: queue.length,
      avgRuntimeSec,
      successRate,
      cpuUsage: Math.min(98, 18 + active.length * 12 + queue.length * 4),
      gpuUsage: Math.min(96, 10 + active.filter((j) => j.studioId).length * 18),
    };
  },
};

export type TaskExecutionApi = typeof taskExecution;

export function lifecycleLabelRu(status: JobLifecycle): string {
  const map: Record<JobLifecycle, string> = {
    running: "Выполняется",
    waiting: "В очереди",
    completed: "Завершено",
    failed: "Ошибка",
    cancelled: "Отменено",
    retrying: "Повтор",
    paused: "Пауза",
  };
  return map[status];
}
