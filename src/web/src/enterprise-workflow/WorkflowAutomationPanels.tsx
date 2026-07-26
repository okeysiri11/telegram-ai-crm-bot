/**
 * Enterprise Workflow Automation panels — Sprint 32.7.
 */

import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveWorkflowAutomation, type WorkflowRun, type WorkflowRunStatus } from "./deriveWorkflowAutomation";
import { BUSINESS_WORKFLOW_TEMPLATES } from "./workflowTemplates";

const STATUS_TONE: Record<WorkflowRunStatus, "default" | "success" | "warning" | "danger"> = {
  active: "success",
  completed: "default",
  waiting: "warning",
  error: "danger",
};

export function WorkflowAutomationWorkspace({ compact = false }: { compact?: boolean }) {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const [params] = useSearchParams();
  const preferred = params.get("wf");
  const bundle = useMemo(
    () => deriveWorkflowAutomation(snapshot, notifications, preferred),
    [snapshot, notifications, preferred],
  );

  if (compact) {
    return (
      <div className="ewf-strip" aria-label="Enterprise Workflow">
        <span className="ewf-strip-label">Workflows</span>
        <Badge tone="success">{bundle.metrics.activeCount} active</Badge>
        <Badge>{bundle.metrics.completedToday} done</Badge>
        <Badge tone={bundle.metrics.errorCount ? "danger" : "success"}>
          err {bundle.metrics.errorCount}
        </Badge>
        <span className="eds-type-small text-[var(--eds-text-muted)]">
          −{bundle.metrics.timeSavedMin} мин
        </span>
        <Link
          to="/platform-builder/workflow-center"
          className="eds-type-small text-[var(--eds-primary)]"
          onClick={() => void telemetry.userActivity("ewf_open_center")}
        >
          Center →
        </Link>
      </div>
    );
  }

  return <WorkflowCenterBody />;
}

export function WorkflowCenterPage() {
  return (
    <WorkspaceLayout>
      <WorkflowCenterBody />
    </WorkspaceLayout>
  );
}

function WorkflowCenterBody() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const [params, setParams] = useSearchParams();
  const preferred = params.get("wf");
  const bundle = useMemo(
    () => deriveWorkflowAutomation(snapshot, notifications, preferred),
    [snapshot, notifications, preferred],
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected =
    bundle.active.concat(bundle.waiting, bundle.errors, bundle.completed).find((r) => r.id === selectedId) ||
    bundle.monitor;

  function selectTemplate(id: string) {
    setParams({ wf: id });
    void telemetry.userActivity(`ewf_template:${id}`);
  }

  return (
    <div className="ewf-center eds-anim-fade">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eds-type-caption uppercase tracking-[0.14em] text-[var(--eds-text-muted)]">
            Enterprise Workflow Automation
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">Workflow Center</h1>
          <p className="mt-1 max-w-2xl eds-type-small text-[var(--eds-text-muted)]">
            Законченные бизнес-процессы AI-команды поверх Mission Control / live-ops — без нового Workflow Engine.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={busy ? "warning" : "success"}>{busy ? "sync…" : "live"}</Badge>
          <Link to="/enterprise-city">
            <Button size="sm" variant="secondary">
              City route
            </Button>
          </Link>
          <Link to="/platform-builder/mission-control">
            <Button size="sm" variant="ghost">
              Mission Control
            </Button>
          </Link>
        </div>
      </header>

      <ExecutiveWorkflowPanel metrics={bundle.metrics} />

      <div className="ewf-grid mt-3">
        <RunListCard
          title="Активные"
          runs={bundle.active}
          onSelect={setSelectedId}
          selectedId={selected?.id}
        />
        <RunListCard
          title="Завершённые"
          runs={bundle.completed}
          onSelect={setSelectedId}
          selectedId={selected?.id}
        />
        <RunListCard
          title="Ожидающие"
          runs={bundle.waiting}
          onSelect={setSelectedId}
          selectedId={selected?.id}
        />
        <RunListCard
          title="С ошибками"
          runs={bundle.errors}
          onSelect={setSelectedId}
          selectedId={selected?.id}
        />
      </div>

      {selected ? (
        <div className="ewf-grid mt-3">
          <WorkflowMonitorPanel run={selected} />
          <WorkflowTimelinePanel run={selected} />
          <AiChainPanel chain={selected.aiChain} />
          <Card title="City Route" className="ewf-card">
            <p className="eds-type-small text-[var(--eds-text-muted)] mb-2">
              Маршрут зданий на Enterprise City
            </p>
            <ol className="ewf-chain">
              {selected.cityPath.map((id, i) => (
                <li key={id}>
                  <Badge>{id}</Badge>
                  {i < selected.cityPath.length - 1 ? <span className="ewf-arrow">↓</span> : null}
                </li>
              ))}
            </ol>
            <div className="mt-3">
              <Link to={`/enterprise-city?wf=${selected.templateId}`}>
                <Button size="sm">Показать на карте</Button>
              </Link>
            </div>
          </Card>
        </div>
      ) : null}

      <Card title="Business Templates" className="mt-3">
        <p className="eds-type-small text-[var(--eds-text-muted)] mb-3">
          Библиотека шаблонов (Hub kinds) — без конструктора процессов.
        </p>
        <div className="ewf-templates">
          {BUSINESS_WORKFLOW_TEMPLATES.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`ewf-template${preferred === t.id ? " is-active" : ""}`}
              onClick={() => selectTemplate(t.id)}
            >
              <span className="font-medium">{t.libraryLabel}</span>
              <span className="block eds-type-small text-[var(--eds-text-muted)]">{t.description}</span>
              <Badge>{t.hubKind}</Badge>
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
}

function ExecutiveWorkflowPanel({
  metrics,
}: {
  metrics: ReturnType<typeof deriveWorkflowAutomation>["metrics"];
}) {
  return (
    <Card title="Executive View · Workflows сегодня" className="ewf-exec">
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5 eds-type-small">
        <li>
          <Badge tone="success">Выполнено {metrics.completedToday}</Badge>
        </li>
        <li>
          <Badge>Автоматизировано {metrics.automated}</Badge>
        </li>
        <li>
          <Badge tone="success">Сэкономлено {metrics.timeSavedMin} мин</Badge>
        </li>
        <li>
          <Badge tone="warning">Активных {metrics.activeCount}</Badge>
        </li>
        <li>
          <Badge tone={metrics.errorCount ? "danger" : "success"}>Ошибок {metrics.errorCount}</Badge>
        </li>
      </ul>
    </Card>
  );
}

function RunListCard({
  title,
  runs,
  onSelect,
  selectedId,
}: {
  title: string;
  runs: WorkflowRun[];
  onSelect: (id: string) => void;
  selectedId?: string;
}) {
  return (
    <Card title={title} className="ewf-card">
      <ul className="space-y-2 eds-type-small">
        {runs.length ? (
          runs.map((r) => (
            <li key={r.id}>
              <button
                type="button"
                className={`ewf-run${selectedId === r.id ? " is-active" : ""}`}
                onClick={() => onSelect(r.id)}
              >
                <span className="font-medium">{r.title}</span>
                <span className="ml-2">
                  <Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge>
                </span>
                <span className="block text-[var(--eds-text-muted)]">
                  {r.currentExecutor} · {r.durationMin} мин
                </span>
              </button>
            </li>
          ))
        ) : (
          <li className="text-[var(--eds-text-muted)]">· Нет процессов</li>
        )}
      </ul>
    </Card>
  );
}

function WorkflowMonitorPanel({ run }: { run: WorkflowRun }) {
  return (
    <Card title="Workflow Monitor" className="ewf-card">
      <ul className="space-y-2 eds-type-small">
        <li>
          Статус: <Badge tone={STATUS_TONE[run.status]}>{run.status}</Badge>
        </li>
        <li>Длительность: {run.durationMin} мин</li>
        <li>Текущий исполнитель: <strong>{run.currentExecutor}</strong></li>
        <li>Следующий шаг: {run.nextStep}</li>
        <li>Результат: {run.result}</li>
        <li className="text-[var(--eds-text-muted)]">Hub kind: {run.hubKind}</li>
      </ul>
    </Card>
  );
}

function WorkflowTimelinePanel({ run }: { run: WorkflowRun }) {
  return (
    <Card title="Workflow Timeline" className="ewf-card">
      <ol className="ewf-chain">
        {run.steps.map((s, i) => (
          <li key={s.id} className={i === run.stepIndex ? "is-current" : i < run.stepIndex ? "is-done" : ""}>
            <span className="font-medium eds-type-small">{s.label}</span>
            {i < run.steps.length - 1 ? <span className="ewf-arrow">↓</span> : null}
          </li>
        ))}
      </ol>
    </Card>
  );
}

function AiChainPanel({ chain }: { chain: string[] }) {
  return (
    <Card title="AI Chain" className="ewf-card">
      <ol className="ewf-chain">
        {chain.map((label, i) => (
          <li key={`${label}_${i}`}>
            <Badge>{label}</Badge>
            {i < chain.length - 1 ? <span className="ewf-arrow">↓</span> : null}
          </li>
        ))}
      </ol>
    </Card>
  );
}
