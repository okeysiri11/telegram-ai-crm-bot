/**
 * Sprint 30.5 — AI Agent Center (unified Agent Runtime surface).
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useAiAgentRuntime, useJobManager } from "@/enterprise-runtime/useRuntimeEngine";
import { DEFAULT_AGENTS } from "@/enterprise-runtime/defaultAgents";
import { aiAgentRuntime } from "@/enterprise-runtime/aiAgentRuntime";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { ORG_SELECTOR_OPTIONS } from "@/navigation/enterpriseRuNav";
import { taskExecution, lifecycleLabelRu } from "./taskExecution";
import { AI_TASK_STAGES, stageLabelRu } from "./taskPipeline";
import { OwnerAiDashboard } from "./OwnerAiDashboard";
import { AgentOsMonitor } from "./AgentOsMonitor";
import type { AiTaskSecurityContext } from "./aiTaskSecurity";
import type { JobPriority, RuntimeJobRecord } from "@/enterprise-runtime/types";

function useSecurityCtx(): AiTaskSecurityContext {
  const orgId = useOrgSelector((s) => s.organizationId);
  const isOwner = useRoleSwitcher((s) => s.isOwnerView());
  const roleId = useRoleSwitcher((s) => s.activeRoleId);
  return useMemo(
    () => ({
      roles: isOwner ? ["owner", roleId] : [roleId || "employee"],
      permissions: isOwner ? ["*", "ai_agents"] : ["ai_agents"],
      orgId: orgId || ORG_SELECTOR_OPTIONS[0]?.id || "org_demo",
      workspaceId: `ws_${orgId || "demo"}`,
      actor: isOwner ? "owner" : roleId || "user",
      tenantId: orgId,
    }),
    [orgId, isOwner, roleId],
  );
}

export function AIAgentCenterPage() {
  const ctx = useSecurityCtx();
  const isOwner = useRoleSwitcher((s) => s.isOwnerView());
  const agents = useAiAgentRuntime();
  const { jobs: runtimeJobs } = useJobManager();
  const [tick, setTick] = useState(0);
  const [taskTitle, setTaskTitle] = useState("Новая AI-задача");
  const [selectedAgent, setSelectedAgent] = useState(DEFAULT_AGENTS[0]?.id || "");
  const [focusJobId, setFocusJobId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    document.title = "AI Agent Center · ADOS";
  }, []);

  const jobs = useMemo(() => {
    void tick;
    void runtimeJobs;
    return taskExecution.list(ctx);
  }, [ctx, tick, runtimeJobs]);

  const dash = useMemo(() => {
    void tick;
    return taskExecution.dashboard(ctx);
  }, [ctx, tick]);

  const health = useMemo(() => aiAgentRuntime.healthSummary(), [agents]);
  const defaults = useMemo(() => aiAgentRuntime.defaultAgents(), [agents]);
  const available = useMemo(
    () => agents.filter((a) => a.status === "idle" || a.status === "waiting"),
    [agents],
  );
  const activeAgents = useMemo(() => agents.filter((a) => a.status === "busy"), [agents]);
  const running = jobs.filter((j) => j.status === "running" || j.status === "paused");
  const completed = jobs.filter((j) => j.status === "completed");
  const queue = jobs.filter((j) => j.status === "waiting" || j.status === "retrying");
  const focus = focusJobId ? jobs.find((j) => j.id === focusJobId) : null;

  async function run(label: string, fn: () => Promise<unknown>) {
    try {
      await fn();
      setMessage(label);
      refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка");
    }
  }

  return (
    <WorkspaceLayout>
      <div className="stack-lg art-page" data-testid="ai-agent-center">
        <header className="art-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">AgentOS · Sprint 32.1 · Runtime SoR</p>
            <h1 className="art-title">Центр AI-агентов</h1>
            <p className="eds-type-body">
              Единый runtime: реестр, lifecycle, messaging, memory, observability. Без изолированных агентов.
            </p>
          </div>
          <div className="art-hero-actions">
            <Link to="/platform-builder/runtime" className="eds-type-small text-[var(--eds-primary)]">
              Runtime →
            </Link>
            <Link to="/production-studio" className="eds-type-small text-[var(--eds-primary)]">
              Production Studio →
            </Link>
            <Link to="/platform-builder/ai-team" className="eds-type-small text-[var(--eds-primary)]">
              AI Team →
            </Link>
          </div>
        </header>

        <AgentOsMonitor />

        <div className="art-dash" aria-label="AI Dashboard">
          <DashCard label="Активные агенты" value={String(activeAgents.length)} />
          <DashCard label="Завершено" value={String(dash.completedTasks)} />
          <DashCard label="Ср. время" value={`${dash.avgRuntimeSec}s`} />
          <DashCard label="Очередь" value={String(dash.queueLength)} />
          <DashCard label="CPU" value={`${dash.cpuUsage}%`} />
          <DashCard label="GPU" value={`${dash.gpuUsage}%`} />
          <DashCard label="Успех" value={`${dash.successRate}%`} />
        </div>

        {isOwner ? <OwnerAiDashboard ctx={ctx} onChanged={refresh} /> : null}

        <div className="art-split">
          <Card aria-label="Active Agents">
            <div className="art-section-head">
              <h2>Активные агенты</h2>
              <Badge tone="success">{activeAgents.length}</Badge>
            </div>
            <ul className="art-queue-list">
              {activeAgents.map((a) => (
                <li key={a.id} className="art-queue-item">
                  <div className="art-queue-top">
                    <strong>{a.name}</strong>
                    <Badge tone="warning">{a.status}</Badge>
                  </div>
                  <p className="eds-type-small text-[var(--eds-muted)]">{a.task || "—"}</p>
                </li>
              ))}
              {!activeAgents.length ? (
                <li className="eds-type-small text-[var(--eds-muted)]">Нет активных агентов</li>
              ) : null}
            </ul>
          </Card>

          <Card aria-label="Available Agents">
            <div className="art-section-head">
              <h2>Доступные агенты</h2>
              <Badge>{available.length}</Badge>
            </div>
            <ul className="art-queue-list">
              {defaults.map((a) => {
                const def = DEFAULT_AGENTS.find((d) => d.id === a.id);
                return (
                  <li key={a.id} className="art-queue-item">
                    <div className="art-queue-top">
                      <strong>{def?.nameRu || a.name}</strong>
                      <Badge tone={a.status === "idle" ? "success" : "default"}>{a.status}</Badge>
                    </div>
                    <p className="eds-type-small text-[var(--eds-muted)]">
                      {def?.profession} · {def?.specialization}
                    </p>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() =>
                        void run("Агент запущен", async () => {
                          const job = await taskExecution.create(ctx, {
                            title: `Задача для ${def?.nameRu || a.name}`,
                            agentId: a.id,
                            priority: "normal",
                          });
                          await taskExecution.start(ctx, job.id);
                          aiAgentRuntime.launch(a.id, job.title);
                          setFocusJobId(job.id);
                        })
                      }
                    >
                      Запустить
                    </Button>
                  </li>
                );
              })}
            </ul>
          </Card>
        </div>

        <Card aria-label="Agent Health">
          <div className="art-section-head">
            <h2>Здоровье агентов</h2>
          </div>
          <div className="art-health-grid">
            <HealthStat label="Всего" value={String(health.total)} />
            <HealthStat label="OK" value={String(health.healthy)} ok />
            <HealthStat label="Warning" value={String(health.warning)} ok={health.warning === 0} />
            <HealthStat label="Critical" value={String(health.critical)} ok={health.critical === 0} />
            <HealthStat label="Busy" value={String(health.busy)} />
          </div>
        </Card>

        <Card title="Создать задачу">
          <div className="row" style={{ gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <Input
              className="min-w-[220px] flex-1"
              value={taskTitle}
              onChange={(e) => setTaskTitle(e.target.value)}
              aria-label="Название задачи"
            />
            <select
              className="eds-input"
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              aria-label="Агент"
            >
              {DEFAULT_AGENTS.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.nameRu}
                </option>
              ))}
            </select>
            <Button
              onClick={() =>
                void run("Задача создана", async () => {
                  const job = await taskExecution.create(ctx, {
                    title: taskTitle.trim() || "AI-задача",
                    agentId: selectedAgent,
                  });
                  setFocusJobId(job.id);
                })
              }
            >
              Создать
            </Button>
          </div>
          {message ? <p className="eds-type-helper mt-2">{message}</p> : null}
        </Card>

        <div className="art-split">
          <TaskList title="Выполняются" items={running} onSelect={setFocusJobId} />
          <TaskList title="Очередь" items={queue} onSelect={setFocusJobId} />
          <TaskList title="Завершённые" items={completed} onSelect={setFocusJobId} />
        </div>

        <Card title="Конвейер этапов">
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            {AI_TASK_STAGES.filter((s) => s.id !== "failed").map((s) => (
              <Badge key={s.id} tone={focus?.stage === s.id ? "success" : "default"}>
                {s.labelRu}
              </Badge>
            ))}
            <Badge tone={focus?.stage === "failed" ? "danger" : "default"}>Ошибка</Badge>
          </div>
        </Card>

        {focus ? (
          <Card title={`Задача · ${focus.title}`}>
            <ul className="eds-type-small space-y-1">
              <li>
                Статус: <strong>{lifecycleLabelRu(focus.status)}</strong>
              </li>
              <li>
                Этап: <strong>{stageLabelRu(focus.stage || "waiting")}</strong>
              </li>
              <li>
                Прогресс: <strong>{focus.progress}%</strong>
              </li>
              <li>
                Приоритет: <strong>{focus.priority || "normal"}</strong>
              </li>
            </ul>
            <div className="row mt-3" style={{ gap: 6, flexWrap: "wrap" }}>
              <Button size="sm" onClick={() => void run("Старт", () => taskExecution.start(ctx, focus.id))}>
                Старт
              </Button>
              <Button size="sm" variant="secondary" onClick={() => void run("Пауза", () => taskExecution.pause(ctx, focus.id))}>
                Пауза
              </Button>
              <Button size="sm" variant="secondary" onClick={() => void run("Продолжить", () => taskExecution.resume(ctx, focus.id))}>
                Продолжить
              </Button>
              <Button size="sm" variant="ghost" onClick={() => void run("Отмена", () => taskExecution.cancel(ctx, focus.id))}>
                Отмена
              </Button>
              <Button size="sm" variant="ghost" onClick={() => void run("Повтор", () => taskExecution.retry(ctx, focus.id))}>
                Повтор
              </Button>
              {(["low", "normal", "high", "critical"] as JobPriority[]).map((p) => (
                <Button
                  key={p}
                  size="sm"
                  variant="ghost"
                  onClick={() => void run(`Приоритет ${p}`, () => taskExecution.setPriority(ctx, focus.id, p))}
                >
                  {p}
                </Button>
              ))}
            </div>
            <div className="mt-4">
              <h3 className="eds-type-section">Логи</h3>
              <ul className="eds-type-small space-y-1 max-h-40 overflow-auto">
                {(focus.logs || []).slice().reverse().map((l, i) => (
                  <li key={`${l.at}_${i}`}>
                    <span className="text-[var(--eds-muted)]">{new Date(l.at).toLocaleTimeString()} · </span>
                    {l.message}
                  </li>
                ))}
                {!focus.logs?.length ? <li className="text-[var(--eds-muted)]">Нет логов</li> : null}
              </ul>
            </div>
            <div className="mt-3">
              <h3 className="eds-type-section">История</h3>
              <ul className="eds-type-small space-y-1 max-h-32 overflow-auto">
                {(focus.history || []).slice().reverse().map((l, i) => (
                  <li key={`h_${l.at}_${i}`}>{l.message}</li>
                ))}
              </ul>
            </div>
          </Card>
        ) : null}
      </div>
    </WorkspaceLayout>
  );
}

function DashCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="art-dash-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function HealthStat({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="art-health-stat">
      <span className="eds-type-caption">{label}</span>
      <strong className={ok === false ? "text-[var(--eds-danger)]" : undefined}>{value}</strong>
    </div>
  );
}

function TaskList({
  title,
  items,
  onSelect,
}: {
  title: string;
  items: RuntimeJobRecord[];
  onSelect: (id: string) => void;
}) {
  return (
    <Card>
      <div className="art-section-head">
        <h2>{title}</h2>
        <Badge>{items.length}</Badge>
      </div>
      <ul className="art-queue-list">
        {items.slice(0, 8).map((j) => (
          <li key={j.id}>
            <button type="button" className="art-queue-item w-full text-left" onClick={() => onSelect(j.id)}>
              <div className="art-queue-top">
                <strong>{j.title}</strong>
                <Badge>{lifecycleLabelRu(j.status)}</Badge>
              </div>
              <span className="eds-type-small text-[var(--eds-muted)]">{j.progress}%</span>
            </button>
          </li>
        ))}
        {!items.length ? <li className="eds-type-small text-[var(--eds-muted)]">Пусто</li> : null}
      </ul>
    </Card>
  );
}
