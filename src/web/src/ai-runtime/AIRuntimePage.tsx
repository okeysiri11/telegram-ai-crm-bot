/**
 * AI Runtime & Orchestration Center UI — Sprint 33.2.
 * Live view of AI task execution — no new Runtime / Queue / Workflow Engine.
 */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveRuntime, ORCH_CHAIN, type RuntimeJobState, type RuntimePriority } from "./deriveRuntime";

const STATE_TONE: Record<RuntimeJobState, "default" | "success" | "warning" | "danger"> = {
  active: "success",
  waiting: "warning",
  completed: "default",
  failed: "danger",
  paused: "warning",
};

const STATE_LABEL: Record<RuntimeJobState, string> = {
  active: "Active",
  waiting: "Waiting",
  completed: "Completed",
  failed: "Failed",
  paused: "Paused",
};

const PRI_LABEL: Record<RuntimePriority, string> = {
  critical: "Critical",
  high: "High",
  normal: "Normal",
  low: "Low",
};

export function AIRuntimePage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const rt = useMemo(() => deriveRuntime(snapshot, notifications), [snapshot, notifications]);

  return (
    <WorkspaceLayout>
      <div className="art-page" data-testid="ai-runtime-center">
        <header className="art-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">AI Runtime & Orchestration · Sprint 33.2</p>
            <h1 className="art-title">Runtime</h1>
            <p className="eds-type-body">
              Как AI выполняет задачи в реальном времени — очередь, оркестрация, health.
            </p>
          </div>
          <div className="art-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Link to="/platform-builder/mission-control" className="eds-type-small text-[var(--eds-primary)]">
              Mission Control →
            </Link>
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Twin →
            </Link>
            <Link to="/platform-builder/workflow-center" className="eds-type-small text-[var(--eds-primary)]">
              Workflows →
            </Link>
          </div>
        </header>

        {/* SECTION 1 — Dashboard */}
        <div className="art-dash" aria-label="Runtime Dashboard">
          {(Object.keys(rt.counts) as RuntimeJobState[]).map((k) => (
            <div key={k} className={`art-dash-card art-dash-card--${k}`}>
              <span>{STATE_LABEL[k]}</span>
              <strong>{rt.counts[k]}</strong>
            </div>
          ))}
        </div>

        {/* SECTION 5 — Health */}
        <Card className="art-health" aria-label="Runtime Health">
          <div className="art-section-head">
            <h2>Runtime Health</h2>
            {rt.health.needsIntervention ? (
              <Badge tone="danger">Intervention needed</Badge>
            ) : (
              <Badge tone="success">Stable</Badge>
            )}
          </div>
          <div className="art-health-grid">
            <HealthStat label="AI Online" value={rt.health.aiOnline ? "Yes" : "No"} ok={rt.health.aiOnline} />
            <HealthStat label="Queue Size" value={String(rt.health.queueSize)} />
            <HealthStat label="Active Executions" value={String(rt.health.activeExecutions)} />
            <HealthStat label="Avg Response" value={`${rt.health.avgResponseMs} ms`} />
            <HealthStat label="Failed Tasks" value={String(rt.health.failedTasks)} ok={rt.health.failedTasks === 0} />
            <HealthStat label="Retries" value={String(rt.health.retries)} />
          </div>
        </Card>

        <div className="art-split">
          {/* SECTION 2 — Live Queue */}
          <Card className="art-queue" aria-label="Live AI Queue">
            <div className="art-section-head">
              <h2>Live AI Queue</h2>
              <span className="eds-type-small text-[var(--eds-muted)]">{rt.queue.length} in flight</span>
            </div>
            <ul className="art-queue-list">
              {rt.queue.map((j) => (
                <li key={j.id} className="art-queue-item">
                  <div className="art-queue-top">
                    <strong>{j.title}</strong>
                    <Badge tone={STATE_TONE[j.state]}>{STATE_LABEL[j.state]}</Badge>
                  </div>
                  <div className="art-queue-meta">
                    <span>Исполнитель: {j.executor}</span>
                    <span>Приоритет: {PRI_LABEL[j.priority]}</span>
                    <span>Источник: {j.source}</span>
                    <span>Ожидание: {j.waitSec}s</span>
                  </div>
                  <div className="art-progress">
                    <div className="art-progress-bar" style={{ width: `${j.progress}%` }} />
                  </div>
                  <span className="eds-type-small text-[var(--eds-muted)]">{j.progress}%</span>
                </li>
              ))}
              {!rt.queue.length ? (
                <li className="eds-type-small text-[var(--eds-muted)]">Очередь пуста</li>
              ) : null}
            </ul>
          </Card>

          {/* SECTION 4 — Execution Monitor */}
          <Card className="art-monitor" aria-label="Execution Monitor">
            <div className="art-section-head">
              <h2>Execution Monitor</h2>
            </div>
            <dl className="art-dl">
              <div>
                <dt>Текущий шаг</dt>
                <dd>{rt.monitor.currentStep}</dd>
              </div>
              <div>
                <dt>Следующий шаг</dt>
                <dd>{rt.monitor.nextStep}</dd>
              </div>
              <div>
                <dt>Затраченное время</dt>
                <dd>{rt.monitor.elapsedSec}s</dd>
              </div>
              <div>
                <dt>Количество AI</dt>
                <dd>{rt.monitor.aiCount}</dd>
              </div>
              <div>
                <dt>Связанные Workflow</dt>
                <dd>
                  <ul>
                    {rt.monitor.workflows.map((w) => (
                      <li key={w}>{w}</li>
                    ))}
                  </ul>
                </dd>
              </div>
            </dl>
            <Link to="/platform-builder/ai-team">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => void telemetry.userActivity("runtime_open_team")}
              >
                AI Team →
              </Button>
            </Link>
          </Card>
        </div>

        {/* SECTION 3 — Orchestration Timeline */}
        <Card className="art-orch" aria-label="Orchestration Timeline">
          <div className="art-section-head">
            <h2>Orchestration Timeline</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">события AI Core / live-ops</span>
          </div>
          <ol className="art-chain">
            {rt.orchestration.map((step, i) => (
              <li key={step.id}>
                <div className={`art-chain-node${step.active ? " is-active" : ""}`}>
                  <strong>{step.label}</strong>
                  <span className="eds-type-small">{step.detail}</span>
                </div>
                {i < ORCH_CHAIN.length - 1 ? <span className="art-chain-arrow" aria-hidden>↓</span> : null}
              </li>
            ))}
          </ol>
        </Card>

        {/* SECTION 6 — Twin link */}
        <Card className="art-twin" aria-label="Digital Twin runtime">
          <div className="art-section-head">
            <h2>Digital Twin</h2>
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Открыть Twin →
            </Link>
          </div>
          <div className="art-twin-grid">
            <div>
              <h3>Процессы сейчас</h3>
              <ul>
                {(rt.twin.processesRunning.length ? rt.twin.processesRunning : ["—"]).map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>AI задействованы</h3>
              <ul>
                {(rt.twin.aiInvolved.length ? rt.twin.aiInvolved : ["—"]).map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Интеграции</h3>
              <ul>
                {(rt.twin.integrationsUsed.length ? rt.twin.integrationsUsed : ["—"]).map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

function HealthStat({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className={`art-health-stat${ok === false ? " is-bad" : ok ? " is-ok" : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

/** Compact shell strip — shared useLiveEnterprise. */

export function RuntimeMonitorCompact() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const rt = useMemo(() => deriveRuntime(snapshot, notifications), [snapshot, notifications]);

  return (
    <Card title="Runtime Monitor" className="art-mc-compact" aria-label="Runtime Monitor">
      <div className="art-mc-row">
        <Badge tone="success">{rt.health.activeExecutions} running</Badge>
        <Badge tone="warning">{rt.health.queueSize} queue</Badge>
        {rt.health.failedTasks ? (
          <Badge tone="danger">{rt.health.failedTasks} errors</Badge>
        ) : (
          <Badge tone="success">no errors</Badge>
        )}
        {rt.health.needsIntervention ? (
          <Badge tone="danger">Intervention</Badge>
        ) : (
          <Badge tone="success">No action</Badge>
        )}
      </div>
      <p className="eds-type-small text-[var(--eds-muted)] mt-2">
        Шаг: {rt.monitor.currentStep} → {rt.monitor.nextStep} · avg {rt.health.avgResponseMs} ms
      </p>
      <Link to="/platform-builder/runtime" className="eds-type-small text-[var(--eds-primary)]">
        Runtime Center →
      </Link>
    </Card>
  );
}
