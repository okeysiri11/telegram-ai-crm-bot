/**
 * Command Runtime Inspector — Sprint 28.7.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { commandRuntime } from "@/runtime/commandRuntime";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

export function CommandRuntimeInspectorPage() {
  const [tick, setTick] = useState(0);
  const snap = commandRuntime.inspectorSnapshot();

  useEffect(() => {
    document.title = "Command Runtime Inspector · ADOS";
    rememberModuleRoute("/command-runtime");
    commandRuntime.startup();
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  void tick;

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Command Runtime Inspector</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.registered.length} commands · Policy {snap.policy.scope}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={() => { commandRuntime.undo(); refresh(); }}>
            Undo
          </Button>
          <Button size="sm" variant="secondary" onClick={() => { commandRuntime.redo(); refresh(); }}>
            Redo
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              if (commandRuntime.macros.isRecording()) {
                commandRuntime.macros.stop();
              } else {
                commandRuntime.macros.record();
              }
              refresh();
            }}
          >
            {commandRuntime.macros.isRecording() ? "Stop Macro" : "Record Macro"}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              if (commandRuntime.macros.draft().length) {
                commandRuntime.macros.save(`Macro ${new Date().toLocaleTimeString()}`);
              }
              refresh();
            }}
          >
            Save Macro
          </Button>
          <Button size="sm" onClick={refresh}>
            Refresh
          </Button>
          <Link to="/command-center" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Command Center →
          </Link>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <Card title="Analytics">
          <ul className="space-y-1 eds-type-helper">
            <li>Executions: {snap.analytics.executionCount}</li>
            <li>Success rate: {Math.round(snap.analytics.successRate * 100)}%</li>
            <li>Failures: {snap.analytics.failures}</li>
            <li>Avg duration: {snap.analytics.avgDurationMs} ms</li>
            <li>AI usage: {snap.analytics.aiUsage}</li>
            <li>
              Favorites: {snap.analytics.favorites.slice(0, 5).join(", ") || "—"}
            </li>
          </ul>
        </Card>

        <Card title="Running">
          {snap.running.length ? (
            <ul className="space-y-1">
              {snap.running.map((id) => (
                <li key={id}>
                  <Badge>{id}</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-helper">Idle</p>
          )}
        </Card>

        <Card title="Policy">
          <ul className="space-y-1 eds-type-helper">
            <li>Scope: {snap.policy.scope}</li>
            <li>User: {snap.policy.userId || "—"}</li>
            <li>Org: {snap.policy.organizationId || "—"}</li>
            <li>Workspace: {snap.policy.workspaceId || "—"}</li>
            <li>Device: {snap.policy.deviceId || "—"}</li>
            <li>Remote: {snap.policy.remoteSessionId || "—"}</li>
          </ul>
        </Card>

        <Card title={`Undo stack (${snap.undo.length})`}>
          <ul className="max-h-48 space-y-1 overflow-auto eds-type-helper">
            {snap.undo.slice(0, 12).map((e) => (
              <li key={e.id}>
                {e.label} → {e.previousPath}
              </li>
            ))}
            {!snap.undo.length ? <li>Empty</li> : null}
          </ul>
        </Card>

        <Card title={`Redo stack (${snap.redo.length})`}>
          <ul className="max-h-48 space-y-1 overflow-auto eds-type-helper">
            {snap.redo.slice(0, 12).map((e) => (
              <li key={e.id}>
                {e.label} · {e.route || e.action}
              </li>
            ))}
            {!snap.redo.length ? <li>Empty</li> : null}
          </ul>
        </Card>

        <Card title={`History (${snap.history.length})`}>
          <ul className="max-h-48 space-y-1 overflow-auto eds-type-helper">
            {snap.history.slice(0, 12).map((e) => (
              <li key={e.id}>
                <Badge tone={e.ok ? "default" : "danger"}>{e.ok ? "ok" : "err"}</Badge> {e.label}
                {e.error ? ` · ${e.error}` : ""}
              </li>
            ))}
          </ul>
        </Card>

        <Card title={`Macros (${snap.macros.length})`}>
          <ul className="max-h-48 space-y-1 overflow-auto">
            {snap.macros.map((m) => (
              <li key={m.id} className="flex items-center justify-between gap-2">
                <span className="eds-type-helper">
                  {m.favorite ? "★ " : ""}
                  {m.name} ({m.steps.length})
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    void commandRuntime.playMacro(m.id).then(refresh);
                  }}
                >
                  Play
                </Button>
              </li>
            ))}
            {!snap.macros.length ? <li className="eds-type-helper">No saved macros</li> : null}
          </ul>
        </Card>

        <Card title={`Registered (${snap.registered.length})`}>
          <ul className="max-h-64 space-y-1 overflow-auto eds-type-helper">
            {snap.registered.slice(0, 40).map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  className="text-left text-[var(--eds-primary)]"
                  onClick={() => {
                    void commandRuntime.execute(c.id).then(refresh);
                  }}
                >
                  {c.id}
                </button>{" "}
                · {c.label}
              </li>
            ))}
          </ul>
        </Card>

        <Card title={`Launcher IDs (${snap.launcher.length})`}>
          <ul className="max-h-64 space-y-1 overflow-auto eds-type-helper">
            {snap.launcher.slice(0, 30).map((l) => (
              <li key={`${l.source}_${l.appId}`}>
                {l.appId} → {l.commandId}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </FullLayout>
  );
}
