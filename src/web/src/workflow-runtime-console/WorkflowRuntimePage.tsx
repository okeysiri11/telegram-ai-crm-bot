/**
 * Workflow Runtime — Sprint 36.2.
 * Designer · Runtime · Executions · Logs · Variables · Versions · Scheduler · Monitoring
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const WORKFLOWS_API = "/api/workflows";

type SectionId =
  | "designer"
  | "runtime"
  | "executions"
  | "logs"
  | "variables"
  | "versions"
  | "scheduler"
  | "monitoring";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "designer", label: "Designer" },
  { id: "runtime", label: "Runtime" },
  { id: "executions", label: "Executions" },
  { id: "logs", label: "Logs" },
  { id: "variables", label: "Variables" },
  { id: "versions", label: "Versions" },
  { id: "scheduler", label: "Scheduler" },
  { id: "monitoring", label: "Monitoring" },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${WORKFLOWS_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function WorkflowRuntimePage() {
  const [section, setSection] = useState<SectionId>("designer");
  const [workflows, setWorkflows] = useState<Array<Record<string, unknown>>>([]);
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [selectedRun, setSelectedRun] = useState<Record<string, unknown> | null>(null);
  const [versions, setVersions] = useState<Array<Record<string, unknown>>>([]);
  const [monitoring, setMonitoring] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [varsJson, setVarsJson] = useState('{"amount": 1000}');

  const refresh = useCallback(async () => {
    setError(null);
    const [w, r, m] = await Promise.all([
      api<{ workflows: Array<Record<string, unknown>> }>("/workflows"),
      api<{ runs: Array<Record<string, unknown>> }>("/runs"),
      api<Record<string, unknown>>("/monitoring"),
    ]);
    setWorkflows(w.workflows || []);
    setRuns(r.runs || []);
    setMonitoring(m);
    if (!selectedId && w.workflows?.length) setSelectedId(String(w.workflows[0].workflow_id));
  }, [selectedId]);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  useEffect(() => {
    if (!selectedId) return;
    api<Record<string, unknown>>(`/workflows/${selectedId}`)
      .then(setSelected)
      .catch((e) => setError(String(e.message || e)));
    api<{ versions: Array<Record<string, unknown>> }>(`/workflows/${selectedId}/versions`)
      .then((d) => setVersions(d.versions || []))
      .catch(() => setVersions([]));
  }, [selectedId]);

  useEffect(() => {
    if (!selectedRunId) {
      setSelectedRun(null);
      return;
    }
    api<Record<string, unknown>>(`/runs/${selectedRunId}`)
      .then(setSelectedRun)
      .catch((e) => setError(String(e.message || e)));
  }, [selectedRunId]);

  async function runSelected() {
    if (!selectedId) return;
    setBusy(true);
    try {
      const variables = JSON.parse(varsJson || "{}");
      const run = await api<Record<string, unknown>>(`/workflows/${selectedId}/execute`, {
        method: "POST",
        body: JSON.stringify({ variables, mode: "sync" }),
      });
      setSelectedRunId(String(run.run_id));
      await refresh();
      setSection("executions");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  async function tickScheduler() {
    setBusy(true);
    try {
      await api("/scheduler/tick", { method: "POST", body: "{}" });
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Workflow Runtime"
      subtitle="Enterprise workflow execution — conditions, loops, parallel, retry, rollback, scheduler."
    >
      <div className="flex flex-wrap gap-2">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSection(s.id)}
            className={`rounded-md border px-3 py-1.5 text-xs ${
              section === s.id
                ? "border-[var(--eds-primary)] bg-[var(--eds-primary)]/10"
                : "border-[var(--eds-border)] bg-[var(--eds-surface)] text-[var(--eds-text-muted)]"
            }`}
          >
            {s.label}
          </button>
        ))}
        <Button type="button" size="sm" onClick={() => refresh()} disabled={busy}>
          Refresh
        </Button>
      </div>

      {error ? (
        <Card className="border-[var(--eds-danger)]/40 bg-[var(--eds-danger)]/5 p-3 text-sm text-[var(--eds-danger)]">
          {error}
        </Card>
      ) : null}

      {(section === "designer" || section === "runtime") && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="space-y-2 p-4">
            <h3 className="eds-type-h3">Workflows</h3>
            {workflows.map((w) => (
              <button
                key={String(w.workflow_id)}
                type="button"
                className="block w-full rounded-md border border-[var(--eds-border)] p-2 text-left text-xs"
                onClick={() => setSelectedId(String(w.workflow_id))}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{String(w.name)}</span>
                  <Badge>{String(w.status)}</Badge>
                </div>
                <p className="text-[var(--eds-text-muted)]">
                  {String(w.workflow_id)} · v{String(w.version)}
                </p>
              </button>
            ))}
          </Card>
          <Card className="space-y-3 p-4">
            <h3 className="eds-type-h3">Designer / Runtime</h3>
            {selected ? (
              <>
                <p className="text-sm">{String(selected.description || "")}</p>
                <pre className="max-h-64 overflow-auto rounded-md bg-[var(--eds-surface)] p-2 text-[10px]">
                  {JSON.stringify(selected.steps, null, 2)}
                </pre>
                <Input value={varsJson} onChange={(e) => setVarsJson(e.target.value)} />
                <Button type="button" disabled={busy} onClick={runSelected}>
                  Execute
                </Button>
              </>
            ) : (
              <p className="text-sm text-[var(--eds-text-muted)]">Select a workflow.</p>
            )}
          </Card>
        </div>
      )}

      {section === "executions" && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="space-y-2 p-4">
            <h3 className="eds-type-h3">Executions</h3>
            {runs
              .slice()
              .reverse()
              .map((r) => (
                <button
                  key={String(r.run_id)}
                  type="button"
                  className="block w-full rounded-md border border-[var(--eds-border)] p-2 text-left text-xs"
                  onClick={() => setSelectedRunId(String(r.run_id))}
                >
                  <div className="flex justify-between gap-2">
                    <span>{String(r.run_id)}</span>
                    <Badge>{String(r.status)}</Badge>
                  </div>
                  <p className="text-[var(--eds-text-muted)]">
                    {String(r.workflow_id)} · {String(r.mode)}
                  </p>
                </button>
              ))}
          </Card>
          <Card className="p-4">
            <h3 className="eds-type-h3">Run detail</h3>
            <pre className="mt-2 max-h-[420px] overflow-auto text-[10px]">
              {selectedRun ? JSON.stringify(selectedRun, null, 2) : "Select a run"}
            </pre>
          </Card>
        </div>
      )}

      {section === "logs" && (
        <Card className="p-4">
          <h3 className="eds-type-h3">Logs</h3>
          <div className="mt-2 max-h-[420px] space-y-1 overflow-auto text-xs">
            {((selectedRun?.logs as Array<Record<string, unknown>>) || []).map((log, i) => (
              <div key={i} className="border-b border-[var(--eds-border)] py-1">
                <Badge>{String(log.event)}</Badge> {String(log.message)}
              </div>
            ))}
            {!selectedRun ? <p className="text-[var(--eds-text-muted)]">Select a run from Executions.</p> : null}
          </div>
        </Card>
      )}

      {section === "variables" && (
        <Card className="p-4">
          <h3 className="eds-type-h3">Variables</h3>
          <pre className="mt-2 text-xs">
            {JSON.stringify(
              (selectedRun?.context as { vars?: unknown } | undefined)?.vars || selected?.variables || {},
              null,
              2,
            )}
          </pre>
        </Card>
      )}

      {section === "versions" && (
        <Card className="space-y-2 p-4">
          <h3 className="eds-type-h3">Versions — {selectedId || "—"}</h3>
          {versions.map((v) => (
            <div key={`${v.workflow_id}-${v.version}`} className="flex justify-between border-b border-[var(--eds-border)] py-2 text-xs">
              <span>v{String(v.version)} — {String(v.changelog || "")}</span>
              {v.is_active ? <Badge tone="success">active</Badge> : <Badge>history</Badge>}
            </div>
          ))}
        </Card>
      )}

      {section === "scheduler" && (
        <Card className="space-y-3 p-4">
          <h3 className="eds-type-h3">Scheduler</h3>
          <p className="text-sm text-[var(--eds-text-muted)]">
            Process due scheduled workflow runs.
          </p>
          <Button type="button" disabled={busy} onClick={tickScheduler}>
            Tick scheduler
          </Button>
        </Card>
      )}

      {section === "monitoring" && monitoring && (
        <div className="grid gap-3 md:grid-cols-4">
          {Object.entries(monitoring).map(([k, v]) => (
            <Card key={k} className="p-4">
              <p className="eds-type-caption text-[var(--eds-text-muted)]">{k}</p>
              <p className="eds-type-h3">{typeof v === "object" ? JSON.stringify(v) : String(v)}</p>
            </Card>
          ))}
        </div>
      )}
    </PlatformBuilderLayout>
  );
}

export default WorkflowRuntimePage;
