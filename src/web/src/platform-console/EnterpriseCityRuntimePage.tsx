/**
 * Enterprise City Runtime — Sprint 37.0.
 * Enterprise Dashboard · Global Search · Platform Health · Service Registry · Activity Center · Command Center · Platform Settings
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const PLATFORM_API = "/api/platform";
export const DASHBOARD_API = "/api/dashboard";
export const SEARCH_API = "/api/search";

type SectionId =
  | "enterprise-dashboard"
  | "global-search"
  | "platform-health"
  | "service-registry"
  | "activity-center"
  | "command-center"
  | "platform-settings";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "enterprise-dashboard", label: "Enterprise Dashboard" },
  { id: "global-search", label: "Global Search" },
  { id: "platform-health", label: "Platform Health" },
  { id: "service-registry", label: "Service Registry" },
  { id: "activity-center", label: "Activity Center" },
  { id: "command-center", label: "Command Center" },
  { id: "platform-settings", label: "Platform Settings" },
];

async function api<T>(base: string, path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function EnterpriseCityRuntimePage() {
  const [section, setSection] = useState<SectionId>("enterprise-dashboard");
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null);
  const [services, setServices] = useState<Array<Record<string, unknown>>>([]);
  const [health, setHealth] = useState<Array<Record<string, unknown>>>([]);
  const [activity, setActivity] = useState<Array<Record<string, unknown>>>([]);
  const [config, setConfig] = useState<Array<Record<string, unknown>>>([]);
  const [hits, setHits] = useState<Array<Record<string, unknown>>>([]);
  const [query, setQuery] = useState("enterprise");
  const [command, setCommand] = useState("open creative factory");
  const [lastCommand, setLastCommand] = useState<Record<string, unknown> | null>(null);
  const [readiness, setReadiness] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    const [dash, svc, hl, act, cfg, ready] = await Promise.all([
      api<Record<string, unknown>>(DASHBOARD_API, ""),
      api<{ services: Array<Record<string, unknown>> }>(PLATFORM_API, "/services"),
      api<{ components: Array<Record<string, unknown>> }>(PLATFORM_API, "/health"),
      api<{ activity: Array<Record<string, unknown>> }>(PLATFORM_API, "/activity"),
      api<{ config: Array<Record<string, unknown>> }>(PLATFORM_API, "/config"),
      api<Record<string, unknown>>(PLATFORM_API, "/readiness"),
    ]);
    setDashboard(dash);
    setServices(svc.services || []);
    setHealth(hl.components || []);
    setActivity(act.activity || []);
    setConfig(cfg.config || []);
    setReadiness(ready);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const runSearch = async () => {
    setBusy(true);
    try {
      const data = await api<{ hits: Array<Record<string, unknown>> }>(
        SEARCH_API,
        `?q=${encodeURIComponent(query)}`,
      );
      setHits(data.hits || []);
      setSection("global-search");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const runCommand = async () => {
    setBusy(true);
    try {
      const data = await api<Record<string, unknown>>(PLATFORM_API, "/command", {
        method: "POST",
        body: JSON.stringify({ text: command, kind: "natural_language" }),
      });
      setLastCommand(data);
      setSection("command-center");
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="Enterprise City Runtime" subtitle="Unified platform operating environment">
      <div className="space-y-4" data-testid="enterprise-city-runtime-console">
        <div className="flex flex-wrap gap-2">
          {SECTIONS.map((s) => (
            <Button
              key={s.id}
              variant={section === s.id ? "primary" : "secondary"}
              size="sm"
              onClick={() => setSection(s.id)}
            >
              {s.label}
            </Button>
          ))}
        </div>

        {error && <Card className="border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</Card>}

        {section === "enterprise-dashboard" && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge>agents {String(dashboard?.active_agents ?? 0)}</Badge>
              <Badge>workflows {String(dashboard?.workflows ?? 0)}</Badge>
              <Badge>projects {String(dashboard?.projects ?? 0)}</Badge>
              <Badge>
                health {String((dashboard?.platform_health as { overall?: string } | undefined)?.overall ?? "—")}
              </Badge>
              <Badge>
                online {String(dashboard?.services_online ?? 0)}/{String(dashboard?.services_total ?? 0)}
              </Badge>
            </div>
            <div className="grid gap-2 md:grid-cols-2">
              {((dashboard?.recommendations as Array<Record<string, unknown>>) || []).map((r) => (
                <Card key={String(r.id)} className="p-3 text-sm">
                  <div className="font-medium">{String(r.title)}</div>
                  <div className="opacity-70">{String(r.reason)}</div>
                </Card>
              ))}
            </div>
            <Card className="p-3 text-sm">
              Readiness: {String(readiness?.ready)} · score {String(readiness?.score)}
            </Card>
            <Button variant="secondary" onClick={refresh}>
              Refresh
            </Button>
          </div>
        )}

        {section === "global-search" && (
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search platform…" />
              <Button disabled={busy} onClick={runSearch}>
                Search
              </Button>
            </div>
            <div className="grid gap-2">
              {hits.map((h) => (
                <Card key={String(h.hit_id)} className="p-3 text-sm">
                  <div className="font-medium">
                    {String(h.title)} · {String(h.kind)}
                  </div>
                  <div className="opacity-70">
                    {String(h.snippet)} → {String(h.route)} ({String(h.score)})
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {section === "platform-health" && (
          <div className="grid gap-2">
            {health.map((h) => (
              <Card key={String(h.component_id)} className="p-3 text-sm flex justify-between">
                <span>{String(h.name)}</span>
                <Badge>{String(h.level)}</Badge>
              </Card>
            ))}
          </div>
        )}

        {section === "service-registry" && (
          <div className="grid gap-2">
            {services.map((s) => (
              <Card key={String(s.service_id)} className="p-3 text-sm">
                <div className="font-medium">{String(s.display_name)}</div>
                <div className="opacity-70">
                  {String(s.category)} · {String(s.route)} · sprint {String(s.sprint || "—")}
                </div>
              </Card>
            ))}
          </div>
        )}

        {section === "activity-center" && (
          <div className="grid gap-2">
            {activity.slice(0, 20).map((a) => (
              <Card key={String(a.activity_id)} className="p-3 text-sm">
                <div className="font-medium">
                  {String(a.action)} · {String(a.module)}
                </div>
                <div className="opacity-70">{String(a.summary)}</div>
              </Card>
            ))}
          </div>
        )}

        {section === "command-center" && (
          <div className="space-y-3">
            <Input value={command} onChange={(e) => setCommand(e.target.value)} placeholder="Natural language command…" />
            <Button disabled={busy} onClick={runCommand}>
              Execute
            </Button>
            {lastCommand && (
              <Card className="p-3">
                <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(lastCommand, null, 2)}</pre>
              </Card>
            )}
          </div>
        )}

        {section === "platform-settings" && (
          <div className="grid gap-2">
            {config.map((c) => (
              <Card key={String(c.key)} className="p-3 text-sm">
                <div className="font-medium">{String(c.key)}</div>
                <div className="opacity-70">
                  {JSON.stringify(c.value)} · {String(c.category)}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
