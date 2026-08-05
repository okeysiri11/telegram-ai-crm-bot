/**
 * Multi-Agent Runtime — Sprint 36.7.
 * Agent Dashboard · Live Execution · Task Graph · Planner · Communication · Statistics
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const MULTI_AGENT_API = "/api/multi-agent";

type SectionId =
  | "agent-dashboard"
  | "live-execution"
  | "task-graph"
  | "planner"
  | "communication"
  | "statistics";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "agent-dashboard", label: "Agent Dashboard" },
  { id: "live-execution", label: "Live Execution" },
  { id: "task-graph", label: "Task Graph" },
  { id: "planner", label: "Planner" },
  { id: "communication", label: "Communication" },
  { id: "statistics", label: "Statistics" },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${MULTI_AGENT_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function MultiAgentRuntimePage() {
  const [section, setSection] = useState<SectionId>("agent-dashboard");
  const [agents, setAgents] = useState<Array<Record<string, unknown>>>([]);
  const [plans, setPlans] = useState<Array<Record<string, unknown>>>([]);
  const [messages, setMessages] = useState<Array<Record<string, unknown>>>([]);
  const [graph, setGraph] = useState<Record<string, unknown> | null>(null);
  const [statistics, setStatistics] = useState<Record<string, unknown> | null>(null);
  const [execution, setExecution] = useState<Record<string, unknown> | null>(null);
  const [goal, setGoal] = useState("Prepare enterprise launch plan");
  const [mode, setMode] = useState("sequential");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    const [ag, pl, msg, g, st] = await Promise.all([
      api<{ agents: Array<Record<string, unknown>> }>("/agents"),
      api<{ plans: Array<Record<string, unknown>> }>("/plans"),
      api<{ messages: Array<Record<string, unknown>> }>("/messages"),
      api<Record<string, unknown>>("/graph"),
      api<Record<string, unknown>>("/statistics"),
    ]);
    setAgents(ag.agents || []);
    setPlans(pl.plans || []);
    setMessages(msg.messages || []);
    setGraph(g);
    setStatistics(st);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const orchestrate = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api<Record<string, unknown>>("/orchestrate", {
        method: "POST",
        body: JSON.stringify({ goal, mode }),
      });
      setExecution(data);
      await refresh();
      setSection("live-execution");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const createPlan = async () => {
    setBusy(true);
    try {
      await api("/plan", { method: "POST", body: JSON.stringify({ goal, mode }) });
      await refresh();
      setSection("planner");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="Multi-Agent Runtime" subtitle="Sprint 36.7 · orchestrate · collaborate · supervise">
      <div className="space-y-4" data-testid="multi-agent-console">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <p className="eds-type-small text-[var(--eds-muted)]">
            Autonomous multi-agent collaboration with planning, messaging, and supervision.
          </p>
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

        <nav className="flex flex-wrap gap-2" aria-label="Multi-Agent sections">
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

        {section === "agent-dashboard" && (
          <Card className="p-4 space-y-2" aria-label="Agent Dashboard">
            <h2 className="text-lg font-medium">Agent Dashboard</h2>
            <ul className="space-y-1 text-sm">
              {agents.map((a) => (
                <li key={String(a.agent_id)} className="flex justify-between gap-2">
                  <span>
                    {String(a.name)} · {String(a.availability)}
                  </span>
                  <Badge tone={a.healthy ? "success" : "warning"}>p{String(a.priority)}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "live-execution" && (
          <Card className="p-4 space-y-3" aria-label="Live Execution">
            <h2 className="text-lg font-medium">Live Execution</h2>
            <div className="flex gap-2 flex-wrap">
              <Input value={goal} onChange={(e) => setGoal(e.target.value)} aria-label="Goal" />
              <Input value={mode} onChange={(e) => setMode(e.target.value)} aria-label="Mode" />
              <Button type="button" onClick={orchestrate} disabled={busy}>
                Orchestrate
              </Button>
            </div>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(execution || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "task-graph" && (
          <Card className="p-4 space-y-2" aria-label="Task Graph">
            <h2 className="text-lg font-medium">Task Graph</h2>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(graph || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "planner" && (
          <Card className="p-4 space-y-3" aria-label="Planner">
            <h2 className="text-lg font-medium">Planner</h2>
            <Button type="button" onClick={createPlan} disabled={busy}>
              Create Plan
            </Button>
            <ul className="space-y-1 text-sm">
              {plans.map((p) => (
                <li key={String(p.plan_id)}>
                  {String(p.mode)} · {String(p.goal).slice(0, 60)} · {String(p.status)}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "communication" && (
          <Card className="p-4 space-y-2" aria-label="Communication">
            <h2 className="text-lg font-medium">Communication</h2>
            <ul className="space-y-1 text-xs font-mono">
              {messages.map((m) => (
                <li key={String(m.message_id)}>
                  {String(m.channel)} · {String(m.source_agent_id)} → {String(m.target_agent_id || m.topic || "—")}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "statistics" && (
          <Card className="p-4 space-y-2" aria-label="Statistics">
            <h2 className="text-lg font-medium">Statistics</h2>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(statistics || {}, null, 2)}
            </pre>
          </Card>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
