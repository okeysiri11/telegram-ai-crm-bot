/**
 * Automation Center — Sprint 28.9.
 * Center · Inspector · Queue · History · Timeline
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { automationEngine } from "@/runtime/automation";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "inspector" | "queue" | "history" | "timeline";

export function AutomationCenterPage() {
  const [tab, setTab] = useState<Tab>("inspector");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return automationEngine.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Automation Center · ADOS";
    rememberModuleRoute("/automation");
    automationEngine.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 2000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const q = snap.stats.queue;

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Automation Center</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.stats.enabled}/{snap.stats.automations} enabled · success{" "}
            {Math.round(snap.stats.history.successRate * 100)}% · avg {snap.stats.history.avgDurationMs}ms
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => void automationEngine.runAutomation("auto_pulse_parallel").then(refresh)}
          >
            Run Pulse
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => void automationEngine.runAutomation("auto_new_client").then(refresh)}
          >
            Run New Client
          </Button>
          <Button size="sm" onClick={refresh}>
            Refresh
          </Button>
          <Link to="/workflow-runtime" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Workflow Runtime →
          </Link>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {(["inspector", "queue", "history", "timeline"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            className={`rounded-md px-3 py-1.5 eds-type-caption capitalize ${
              tab === t
                ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]"
                : "text-[var(--eds-text-muted)]"
            }`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "inspector" ? (
        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <Card title="Live queue">
            <ul className="space-y-1 eds-type-helper">
              <li>Pending: {q.pending}</li>
              <li>Running: {q.running}</li>
              <li>Waiting: {q.waiting}</li>
              <li>Retry: {q.retry}</li>
              <li>Completed: {q.completed}</li>
              <li>Failed: {q.failed}</li>
              <li>Cancelled: {q.cancelled}</li>
            </ul>
          </Card>
          <Card title="Retry / success statistics">
            <ul className="space-y-1 eds-type-helper">
              <li>History total: {snap.stats.history.total}</li>
              <li>Success rate: {Math.round(snap.stats.history.successRate * 100)}%</li>
              <li>Failure rate: {Math.round(snap.stats.history.failureRate * 100)}%</li>
              <li>Retries: {snap.stats.history.retries}</li>
              <li>Avg duration: {snap.stats.history.avgDurationMs} ms</li>
              <li>Schedules: {snap.stats.schedules}</li>
              <li>Paused automations: {snap.stats.paused}</li>
            </ul>
          </Card>
          <Card title="Registered automations">
            <ul className="max-h-72 space-y-2 overflow-auto">
              {snap.automations.map((a) => (
                <li key={a.id} className="rounded-md border border-[var(--eds-border)] p-2">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <Badge tone={a.enabled ? "success" : "default"}>{a.enabled ? "on" : "off"}</Badge>
                    <span className="eds-type-helper font-medium">{a.name}</span>
                  </div>
                  <p className="eds-type-helper mb-2">
                    → {a.workflowId} · triggers {a.triggers.map((t) => t.kind).join(", ")}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => void automationEngine.runAutomation(a.id).then(refresh)}
                    >
                      Run
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        automationEngine.pauseAutomation(a.id);
                        refresh();
                      }}
                    >
                      Pause
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        automationEngine.resumeAutomation(a.id);
                        refresh();
                      }}
                    >
                      Resume
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      ) : null}

      {tab === "queue" ? (
        <Card title="Automation Queue">
          <ul className="space-y-2">
            {snap.queue.map((j) => (
              <li key={j.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--eds-border)] py-2">
                <div className="eds-type-helper">
                  <Badge
                    tone={
                      j.status === "failed"
                        ? "danger"
                        : j.status === "completed"
                          ? "success"
                          : j.status === "running"
                            ? "info"
                            : "default"
                    }
                  >
                    {j.status}
                  </Badge>{" "}
                  {j.automationId} · {j.triggerKind} · attempt {j.attempt}
                  {j.durationMs != null ? ` · ${j.durationMs}ms` : ""}
                  {j.error ? ` · ${j.error}` : ""}
                </div>
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      automationEngine.cancelAutomation(j.id);
                      refresh();
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void automationEngine.retryAutomation(j.id).then(refresh)}
                  >
                    Retry
                  </Button>
                </div>
              </li>
            ))}
            {!snap.queue.length ? <li className="eds-type-helper">Queue empty</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "history" ? (
        <Card title="Automation History">
          <ul className="space-y-1">
            {snap.history.map((h) => (
              <li key={h.id} className="eds-type-helper">
                <Badge tone={h.status === "failed" ? "danger" : "default"}>{h.status}</Badge> {h.automationId} ·{" "}
                {h.triggerKind} · attempt {h.attempt}
                {h.durationMs != null ? ` · ${h.durationMs}ms` : ""}
                {h.error ? ` · ${h.error}` : ""}
              </li>
            ))}
            {!snap.history.length ? <li className="eds-type-helper">No history yet</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "timeline" ? (
        <Card title="Execution Timeline">
          <ul className="max-h-[28rem] space-y-1 overflow-auto">
            {snap.timeline.map((t) => (
              <li key={t.id} className="eds-type-helper">
                {t.at.slice(11, 19)} · [{t.type}] {t.automationId} / {t.jobId}: {t.message}
              </li>
            ))}
            {!snap.timeline.length ? <li className="eds-type-helper">No events</li> : null}
          </ul>
        </Card>
      ) : null}
    </FullLayout>
  );
}
