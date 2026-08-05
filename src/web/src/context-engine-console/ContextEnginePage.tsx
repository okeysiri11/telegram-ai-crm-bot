/**
 * Enterprise Context Engine — Sprint 36.4.
 * Context Explorer · Sources · Graph · Cache · Sessions · Statistics · Permissions
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const CONTEXT_API = "/api/context-engine";

type SectionId =
  | "context-explorer"
  | "sources"
  | "graph"
  | "cache"
  | "sessions"
  | "statistics"
  | "permissions";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "context-explorer", label: "Context Explorer" },
  { id: "sources", label: "Sources" },
  { id: "graph", label: "Graph" },
  { id: "cache", label: "Cache" },
  { id: "sessions", label: "Sessions" },
  { id: "statistics", label: "Statistics" },
  { id: "permissions", label: "Permissions" },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${CONTEXT_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function ContextEnginePage() {
  const [section, setSection] = useState<SectionId>("context-explorer");
  const [sources, setSources] = useState<Array<Record<string, unknown>>>([]);
  const [sessions, setSessions] = useState<Array<Record<string, unknown>>>([]);
  const [cache, setCache] = useState<Array<Record<string, unknown>>>([]);
  const [cacheStats, setCacheStats] = useState<Record<string, unknown> | null>(null);
  const [permissions, setPermissions] = useState<Array<Record<string, unknown>>>([]);
  const [statistics, setStatistics] = useState<Record<string, unknown> | null>(null);
  const [graph, setGraph] = useState<Record<string, unknown> | null>(null);
  const [bundle, setBundle] = useState<Record<string, unknown> | null>(null);
  const [query, setQuery] = useState("enterprise context");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    const [src, sess, c, perm, stats, g] = await Promise.all([
      api<{ sources: Array<Record<string, unknown>> }>("/sources"),
      api<{ sessions: Array<Record<string, unknown>> }>("/sessions"),
      api<{ entries: Array<Record<string, unknown>>; stats: Record<string, unknown> }>("/cache"),
      api<{ permissions: Array<Record<string, unknown>> }>("/permissions"),
      api<Record<string, unknown>>("/statistics"),
      api<Record<string, unknown>>("/graph"),
    ]);
    setSources(src.sources || []);
    setSessions(sess.sessions || []);
    setCache(c.entries || []);
    setCacheStats(c.stats || null);
    setPermissions(perm.permissions || []);
    setStatistics(stats);
    setGraph(g);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const resolve = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api<Record<string, unknown>>("/resolve", {
        method: "POST",
        body: JSON.stringify({ query, create_session: true, use_cache: true, max_tokens: 1024 }),
      });
      setBundle(data);
      await refresh();
      setSection("context-explorer");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="Context Engine" subtitle="Sprint 36.4 · aggregate · filter · optimize">
      <div className="space-y-4" data-testid="context-engine-console">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <p className="eds-type-small text-[var(--eds-muted)]">
            Collect, merge, and deliver enterprise context to AI Runtime, Workflows, and Services.
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

        <nav className="flex flex-wrap gap-2" aria-label="Context Engine sections">
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

        {section === "context-explorer" && (
          <Card className="p-4 space-y-3" aria-label="Context Explorer">
            <h2 className="text-lg font-medium">Context Explorer</h2>
            <div className="flex gap-2 flex-wrap">
              <Input value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Query" />
              <Button type="button" onClick={resolve} disabled={busy}>
                Resolve
              </Button>
            </div>
            {bundle ? (
              <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
                {JSON.stringify(bundle, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-[var(--eds-muted)]">Resolve a query to inspect the context bundle.</p>
            )}
          </Card>
        )}

        {section === "sources" && (
          <Card className="p-4 space-y-2" aria-label="Sources">
            <h2 className="text-lg font-medium">Sources</h2>
            <ul className="space-y-1">
              {sources.map((s) => (
                <li key={String(s.source)} className="text-sm flex justify-between gap-2">
                  <span>
                    {String(s.source)} · rank {String(s.rank)}
                  </span>
                  <Badge tone={s.enabled ? "success" : "warning"}>{String(s.fragment_count)} frags</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "graph" && (
          <Card className="p-4 space-y-2" aria-label="Graph">
            <h2 className="text-lg font-medium">Graph</h2>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(graph || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "cache" && (
          <Card className="p-4 space-y-2" aria-label="Cache">
            <h2 className="text-lg font-medium">Cache</h2>
            <p className="text-sm text-[var(--eds-muted)]">{JSON.stringify(cacheStats || {})}</p>
            <ul className="space-y-1 text-xs font-mono">
              {cache.map((e) => (
                <li key={String(e.cache_key)}>
                  {String(e.cache_key).slice(0, 16)}… · hits {String(e.hits)} · tokens {String(e.token_count)}
                </li>
              ))}
            </ul>
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

        {section === "statistics" && (
          <Card className="p-4 space-y-2" aria-label="Statistics">
            <h2 className="text-lg font-medium">Statistics</h2>
            <pre className="text-xs overflow-auto bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(statistics || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "permissions" && (
          <Card className="p-4 space-y-2" aria-label="Permissions">
            <h2 className="text-lg font-medium">Permissions</h2>
            <ul className="space-y-1 text-sm">
              {permissions.map((p) => (
                <li key={String(p.permission_id)}>
                  {String(p.principal)} → {String(p.source)} · {String(p.action)} · max {String(p.max_sensitivity)}
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
