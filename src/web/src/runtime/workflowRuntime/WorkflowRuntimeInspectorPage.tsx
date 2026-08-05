/**
 * Workflow Runtime Inspector — Sprint 28.8.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { rememberModuleRoute } from "@/modules/lastModuleStore";
import type { WorkflowSession } from "@/runtime/workflowRuntime";

export function WorkflowRuntimeInspectorPage() {
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return workflowRuntime.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Workflow Runtime · ADOS";
    rememberModuleRoute("/workflow-runtime");
    workflowRuntime.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 2000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  async function startDef(id: string) {
    await workflowRuntime.start(id, { surface: "inspector" });
    refresh();
  }

  function graph(session: WorkflowSession) {
    const def = snap.definitions.find((d) => d.id === session.definitionId);
    if (!def) return null;
    return Object.values(def.nodes).map((n) => {
      const rec = session.nodeRecords[n.id];
      return (
        <li key={n.id} className="eds-type-helper">
          <Badge tone={rec?.status === "failed" ? "danger" : rec?.status === "done" ? "success" : "info"}>
            {rec?.status || "pending"}
          </Badge>{" "}
          {n.id} · {n.kind} · {n.label}
          {rec?.durationMs != null ? ` · ${rec.durationMs}ms` : ""}
          {rec?.retryCount ? ` · retries ${rec.retryCount}` : ""}
        </li>
      );
    });
  }

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Workflow Runtime</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.stats.definitions} definitions · {snap.stats.active} running ·{" "}
            ~{snap.stats.memoryEstimateKb} KB
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={() => void startDef("demo_parallel_ops")}>
            Start Parallel Demo
          </Button>
          <Button size="sm" variant="secondary" onClick={() => void startDef("demo_approval_gate")}>
            Start Approval Demo
          </Button>
          <Button size="sm" variant="secondary" onClick={() => void startDef("tpl_new_client")}>
            Start New Client
          </Button>
          <Button size="sm" onClick={refresh}>
            Refresh
          </Button>
          <Link to="/command-runtime" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Command Inspector →
          </Link>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <Card title="Runtime statistics">
          <ul className="space-y-1 eds-type-helper">
            <li>Active: {snap.stats.active}</li>
            <li>Waiting: {snap.stats.waiting}</li>
            <li>Paused: {snap.stats.paused}</li>
            <li>Completed (history): {snap.stats.completed}</li>
            <li>Failed (history): {snap.stats.failed}</li>
            <li>Event queue (workflow_update): {snap.eventQueueHint.length}</li>
          </ul>
        </Card>

        <Card title="Definitions">
          <ul className="max-h-56 space-y-1 overflow-auto">
            {snap.definitions.map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-2">
                <span className="eds-type-helper truncate">
                  {d.name} <span className="opacity-60">({d.id})</span>
                </span>
                <Button size="sm" variant="ghost" onClick={() => void startDef(d.id)}>
                  Start
                </Button>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Event bus (recent workflow_update)">
          <ul className="max-h-56 space-y-1 overflow-auto eds-type-helper">
            {snap.eventQueueHint.map((e, i) => (
              <li key={`${e.at}_${i}`}>
                {e.at.slice(11, 19)} · {JSON.stringify(e.payload).slice(0, 80)}
              </li>
            ))}
            {!snap.eventQueueHint.length ? <li>Empty</li> : null}
          </ul>
        </Card>

        <Card title={`Sessions (${snap.sessions.length})`}>
          <ul className="max-h-80 space-y-3 overflow-auto">
            {snap.sessions.map((s) => (
              <li key={s.id} className="rounded-md border border-[var(--eds-border)] p-2">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <Badge>{s.status}</Badge>
                  <span className="eds-type-helper">{s.definitionId}</span>
                  <span className="eds-type-helper opacity-60">{s.id}</span>
                </div>
                <div className="mb-2 flex flex-wrap gap-1">
                  <Button size="sm" variant="ghost" onClick={() => { workflowRuntime.pause(s.id); refresh(); }}>
                    Pause
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void workflowRuntime.resume(s.id).then(refresh)}
                  >
                    Resume
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void workflowRuntime.approve(s.id, true).then(refresh)}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      workflowRuntime.cancel(s.id);
                      refresh();
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void workflowRuntime.restart(s.id).then(refresh)}
                  >
                    Restart
                  </Button>
                </div>
                <p className="eds-type-helper mb-1">Execution graph</p>
                <ul className="mb-2 space-y-0.5">{graph(s)}</ul>
                <p className="eds-type-helper mb-1">Logs</p>
                <ul className="max-h-24 space-y-0.5 overflow-auto eds-type-helper">
                  {s.logs.slice(0, 8).map((l) => (
                    <li key={l.id}>
                      [{l.level}] {l.message}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
            {!snap.sessions.length ? <li className="eds-type-helper">No active sessions</li> : null}
          </ul>
        </Card>

        <Card title="History">
          <ul className="max-h-80 space-y-1 overflow-auto">
            {snap.history.map((h) => (
              <li key={h.id} className="flex items-center justify-between gap-2 eds-type-helper">
                <span>
                  <Badge tone={h.status === "failed" ? "danger" : "default"}>{h.status}</Badge> {h.name}
                  {h.durationMs != null ? ` · ${h.durationMs}ms` : ""}
                </span>
                <Button size="sm" variant="ghost" onClick={() => void workflowRuntime.replay(h.id).then(refresh)}>
                  Replay
                </Button>
              </li>
            ))}
            {!snap.history.length ? <li className="eds-type-helper">Empty</li> : null}
          </ul>
        </Card>

        <Card title="Debug">
          <ul className="space-y-1 eds-type-helper">
            <li>Waiting nodes: {snap.sessions.filter((s) => s.status === "waiting").length}</li>
            <li>
              Approval pending: {snap.sessions.filter((s) => s.approvalPending).length}
            </li>
            <li>Snapshots: sessions persist to ews_workflow_runtime_v1</li>
            <li>AI path: Command Runtime → start_workflow → Workflow Runtime</li>
            <li>
              Automations:{" "}
              <Link to="/automation" className="text-[var(--eds-primary)]">
                Automation Center →
              </Link>
            </li>
          </ul>
        </Card>
      </div>
    </FullLayout>
  );
}
