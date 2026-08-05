/**
 * AI Runtime Console — Sprint 36.3.
 * Providers · Models · Runtime · Sessions · Prompt Studio · Tool Registry · Execution Logs · Monitoring
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const AI_RUNTIME_API = "/api/ai-runtime";

type SectionId =
  | "providers"
  | "models"
  | "runtime"
  | "sessions"
  | "prompt-studio"
  | "tool-registry"
  | "execution-logs"
  | "monitoring";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "providers", label: "Providers" },
  { id: "models", label: "Models" },
  { id: "runtime", label: "Runtime" },
  { id: "sessions", label: "Sessions" },
  { id: "prompt-studio", label: "Prompt Studio" },
  { id: "tool-registry", label: "Tool Registry" },
  { id: "execution-logs", label: "Execution Logs" },
  { id: "monitoring", label: "Monitoring" },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${AI_RUNTIME_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function AIRuntimeConsolePage() {
  const [section, setSection] = useState<SectionId>("providers");
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [models, setModels] = useState<Array<Record<string, unknown>>>([]);
  const [sessions, setSessions] = useState<Array<Record<string, unknown>>>([]);
  const [prompts, setPrompts] = useState<Array<Record<string, unknown>>>([]);
  const [tools, setTools] = useState<Array<Record<string, unknown>>>([]);
  const [logs, setLogs] = useState<Array<Record<string, unknown>>>([]);
  const [executions, setExecutions] = useState<Array<Record<string, unknown>>>([]);
  const [monitoring, setMonitoring] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [promptText, setPromptText] = useState("Summarize enterprise status");
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    const [st, p, m, s, pr, t, l, e, mon] = await Promise.all([
      api<Record<string, unknown>>("/status"),
      api<{ providers: Array<Record<string, unknown>> }>("/providers"),
      api<{ models: Array<Record<string, unknown>> }>("/models"),
      api<{ sessions: Array<Record<string, unknown>> }>("/sessions"),
      api<{ prompts: Array<Record<string, unknown>> }>("/prompts"),
      api<{ tools: Array<Record<string, unknown>> }>("/tools"),
      api<{ logs: Array<Record<string, unknown>> }>("/logs"),
      api<{ executions: Array<Record<string, unknown>> }>("/tool-executions"),
      api<Record<string, unknown>>("/monitoring"),
    ]);
    setStatus(st);
    setProviders(p.providers || []);
    setModels(m.models || []);
    setSessions(s.sessions || []);
    setPrompts(pr.prompts || []);
    setTools(t.tools || []);
    setLogs(l.logs || []);
    setExecutions(e.executions || []);
    setMonitoring(mon);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const runComplete = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api<Record<string, unknown>>("/complete", {
        method: "POST",
        body: JSON.stringify({ prompt: promptText, create_session: true, use_cache: false }),
      });
      setLastResult(data);
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="AI Runtime" subtitle="Sprint 36.3 · providers · prompts · tools">
      <div className="space-y-4" data-testid="ai-runtime-console">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">Multi-provider inference, prompts, tools, sessions, and audit.</p>
          </div>
          <div className="flex gap-2 items-center">
            {busy ? <Badge>busy…</Badge> : <Badge tone="success">ready</Badge>}
            <Button type="button" onClick={() => refresh().catch((e) => setError(String(e.message || e)))}>
              Refresh
            </Button>
          </div>
        </header>

        {error ? (
          <Card className="p-3 text-[var(--eds-danger)]" role="alert">
            {error}
          </Card>
        ) : null}

        <nav className="flex flex-wrap gap-2" aria-label="AI Runtime sections">
          {SECTIONS.map((s) => (
            <Button
              key={s.id}
              type="button"
              variant={section === s.id ? "primary" : "ghost"}
              onClick={() => setSection(s.id)}
            >
              {s.label}
            </Button>
          ))}
        </nav>

        {section === "providers" && (
          <Card className="p-4 space-y-2" aria-label="Providers">
            <h2 className="text-lg font-medium">Providers</h2>
            <ul className="space-y-1">
              {providers.map((p) => (
                <li key={String(p.provider_id)} className="flex justify-between gap-2 text-sm">
                  <span>
                    {String(p.name)} ({String(p.provider_id)})
                  </span>
                  <Badge tone={p.enabled ? "success" : "warning"}>{String(p.status)}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "models" && (
          <Card className="p-4 space-y-2" aria-label="Models">
            <h2 className="text-lg font-medium">Models</h2>
            <ul className="space-y-1 max-h-96 overflow-auto">
              {models.map((m) => (
                <li key={`${m.provider_id}:${m.model_id}`} className="text-sm">
                  <strong>{String(m.display_name)}</strong> · {String(m.provider_id)}/{String(m.model_id)}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "runtime" && (
          <Card className="p-4 space-y-3" aria-label="Runtime">
            <h2 className="text-lg font-medium">Runtime</h2>
            <p className="text-sm text-[var(--eds-muted)]">
              Default provider: {String(status?.default_provider || "—")} · Fallback:{" "}
              {Array.isArray(status?.fallback_chain) ? (status?.fallback_chain as string[]).join(" → ") : "—"}
            </p>
            <Input value={promptText} onChange={(e) => setPromptText(e.target.value)} aria-label="Prompt" />
            <Button type="button" onClick={runComplete} disabled={busy}>
              Run complete
            </Button>
            {lastResult ? (
              <pre className="text-xs overflow-auto max-h-64 bg-[var(--eds-surface)] p-2 rounded">
                {JSON.stringify(lastResult, null, 2)}
              </pre>
            ) : null}
          </Card>
        )}

        {section === "sessions" && (
          <Card className="p-4 space-y-2" aria-label="Sessions">
            <h2 className="text-lg font-medium">Sessions</h2>
            <ul className="space-y-1">
              {sessions.map((s) => (
                <li key={String(s.session_id)} className="text-sm flex justify-between">
                  <span>{String(s.session_id)}</span>
                  <Badge>{String(s.status)}</Badge>
                </li>
              ))}
              {!sessions.length ? <li className="text-sm text-[var(--eds-muted)]">No sessions yet</li> : null}
            </ul>
          </Card>
        )}

        {section === "prompt-studio" && (
          <Card className="p-4 space-y-2" aria-label="Prompt Studio">
            <h2 className="text-lg font-medium">Prompt Studio</h2>
            <ul className="space-y-1">
              {prompts.map((p) => (
                <li key={String(p.template_id)} className="text-sm">
                  <strong>{String(p.name)}</strong> · v{String(p.version)} · {String(p.template_id)}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "tool-registry" && (
          <Card className="p-4 space-y-2" aria-label="Tool Registry">
            <h2 className="text-lg font-medium">Tool Registry</h2>
            <ul className="space-y-1">
              {tools.map((t) => (
                <li key={String(t.tool_id)} className="text-sm flex justify-between gap-2">
                  <span>
                    {String(t.name)} — {String(t.description)}
                  </span>
                  {t.mcp_compatible ? <Badge tone="success">MCP</Badge> : null}
                </li>
              ))}
            </ul>
            <h3 className="text-sm font-medium pt-2">Recent tool executions</h3>
            <ul className="space-y-1 text-xs">
              {executions.slice(-10).reverse().map((ex) => (
                <li key={String(ex.execution_id)}>
                  {String(ex.tool_id)} · {ex.success ? "ok" : "fail"} · {String(ex.duration_ms)}ms
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "execution-logs" && (
          <Card className="p-4 space-y-2" aria-label="Execution Logs">
            <h2 className="text-lg font-medium">Execution Logs</h2>
            <ul className="space-y-1 max-h-96 overflow-auto text-xs font-mono">
              {logs.slice().reverse().map((l) => (
                <li key={String(l.log_id)}>
                  [{String(l.level)}] {String(l.message)} {l.session_id ? `· ${String(l.session_id)}` : ""}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "monitoring" && (
          <Card className="p-4 space-y-2" aria-label="Monitoring">
            <h2 className="text-lg font-medium">Monitoring</h2>
            <pre className="text-xs overflow-auto bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(monitoring || {}, null, 2)}
            </pre>
          </Card>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
