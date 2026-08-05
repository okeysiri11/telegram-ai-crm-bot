/**
 * Project Memory Engine — Sprint 36.5.
 * Memory Dashboard · Search · Timeline · Relations Graph · Sessions · Analytics
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const PROJECT_MEMORY_API = "/api/project-memory";

type SectionId =
  | "memory-dashboard"
  | "search"
  | "timeline"
  | "relations-graph"
  | "sessions"
  | "analytics";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "memory-dashboard", label: "Memory Dashboard" },
  { id: "search", label: "Search" },
  { id: "timeline", label: "Timeline" },
  { id: "relations-graph", label: "Relations Graph" },
  { id: "sessions", label: "Sessions" },
  { id: "analytics", label: "Analytics" },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${PROJECT_MEMORY_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function ProjectMemoryPage() {
  const [section, setSection] = useState<SectionId>("memory-dashboard");
  const [memories, setMemories] = useState<Array<Record<string, unknown>>>([]);
  const [sessions, setSessions] = useState<Array<Record<string, unknown>>>([]);
  const [timeline, setTimeline] = useState<Array<Record<string, unknown>>>([]);
  const [graph, setGraph] = useState<Record<string, unknown> | null>(null);
  const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);
  const [hits, setHits] = useState<Array<Record<string, unknown>>>([]);
  const [query, setQuery] = useState("project memory semantic");
  const [title, setTitle] = useState("Agent note");
  const [content, setContent] = useState("Remember to prefer platform_memory SoR.");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    const [mem, sess, tl, g, an] = await Promise.all([
      api<{ memories: Array<Record<string, unknown>> }>("/memories"),
      api<{ sessions: Array<Record<string, unknown>> }>("/sessions"),
      api<{ timeline: Array<Record<string, unknown>> }>("/timeline"),
      api<Record<string, unknown>>("/graph"),
      api<Record<string, unknown>>("/analytics"),
    ]);
    setMemories(mem.memories || []);
    setSessions(sess.sessions || []);
    setTimeline(tl.timeline || []);
    setGraph(g);
    setAnalytics(an);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const search = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api<{ hits: Array<Record<string, unknown>> }>("/search", {
        method: "POST",
        body: JSON.stringify({ query, limit: 10 }),
      });
      setHits(data.hits || []);
      setSection("search");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const remember = async () => {
    setBusy(true);
    setError(null);
    try {
      await api("/remember", {
        method: "POST",
        body: JSON.stringify({
          kind: "agent",
          layer: "working",
          title,
          content,
          agent_id: "agent_ui",
          project_id: "proj_ados",
        }),
      });
      await refresh();
      setSection("memory-dashboard");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const createSession = async () => {
    setBusy(true);
    try {
      await api("/sessions", {
        method: "POST",
        body: JSON.stringify({ project_id: "proj_ados", agent_id: "agent_ui" }),
      });
      await refresh();
      setSection("sessions");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="Project Memory" subtitle="Sprint 36.5 · registry · semantic · layers">
      <div className="space-y-4" data-testid="project-memory-console">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <p className="eds-type-small text-[var(--eds-muted)]">
            Long-term semantic memory for projects, agents, clients, workflows, and documents.
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

        <nav className="flex flex-wrap gap-2" aria-label="Project Memory sections">
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

        {section === "memory-dashboard" && (
          <Card className="p-4 space-y-3" aria-label="Memory Dashboard">
            <h2 className="text-lg font-medium">Memory Dashboard</h2>
            <div className="flex gap-2 flex-wrap">
              <Input value={title} onChange={(e) => setTitle(e.target.value)} aria-label="Title" />
              <Input value={content} onChange={(e) => setContent(e.target.value)} aria-label="Content" />
              <Button type="button" onClick={remember} disabled={busy}>
                Remember
              </Button>
            </div>
            <ul className="space-y-1 text-sm">
              {memories.map((m) => (
                <li key={String(m.memory_id)} className="flex justify-between gap-2">
                  <span>
                    {String(m.kind)} · {String(m.layer)} · {String(m.title || m.memory_id)}
                  </span>
                  <Badge>{String(m.importance)}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "search" && (
          <Card className="p-4 space-y-3" aria-label="Search">
            <h2 className="text-lg font-medium">Search</h2>
            <div className="flex gap-2 flex-wrap">
              <Input value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Query" />
              <Button type="button" onClick={search} disabled={busy}>
                Semantic Search
              </Button>
            </div>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(hits, null, 2)}
            </pre>
          </Card>
        )}

        {section === "timeline" && (
          <Card className="p-4 space-y-2" aria-label="Timeline">
            <h2 className="text-lg font-medium">Timeline</h2>
            <ul className="space-y-1 text-xs font-mono">
              {timeline.map((e) => (
                <li key={String(e.history_id)}>
                  {String(e.action)} · {String(e.memory_id || e.session_id || "—")}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "relations-graph" && (
          <Card className="p-4 space-y-2" aria-label="Relations Graph">
            <h2 className="text-lg font-medium">Relations Graph</h2>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(graph || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "sessions" && (
          <Card className="p-4 space-y-3" aria-label="Sessions">
            <h2 className="text-lg font-medium">Sessions</h2>
            <Button type="button" onClick={createSession} disabled={busy}>
              New Session
            </Button>
            <ul className="space-y-1 text-sm">
              {sessions.map((s) => (
                <li key={String(s.session_id)}>
                  {String(s.session_id)} · working_set {Array.isArray(s.working_set) ? s.working_set.length : 0}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "analytics" && (
          <Card className="p-4 space-y-2" aria-label="Analytics">
            <h2 className="text-lg font-medium">Analytics</h2>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(analytics || {}, null, 2)}
            </pre>
          </Card>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
