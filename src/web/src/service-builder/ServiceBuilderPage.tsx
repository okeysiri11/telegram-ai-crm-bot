/**
 * Enterprise Service Builder — Sprint 36.0.
 * Catalog / lifecycle / dependencies / health / permissions / logs / versions.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const SERVICE_BUILDER_API = "/api/service-builder";

export type ServiceCard = {
  id: string;
  name: string;
  display_name: string;
  version: string;
  status: string;
  state: string;
  owner: string;
  category: string;
  icon: string;
  cpu: number;
  ram: number;
  uptime: number;
  dependencies: string[];
  last_update: number;
  restart_count?: number;
  availability_pct?: number;
  response_time_ms?: number;
  error_count?: number;
  permissions?: Record<string, string[]>;
  configuration?: Record<string, unknown>;
  description?: string;
};

type SectionId =
  | "catalog"
  | "installed"
  | "running"
  | "dependencies"
  | "health"
  | "configuration"
  | "permissions"
  | "logs"
  | "versions";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "catalog", label: "Service Catalog" },
  { id: "installed", label: "Installed" },
  { id: "running", label: "Running" },
  { id: "dependencies", label: "Dependencies" },
  { id: "health", label: "Health Monitor" },
  { id: "configuration", label: "Configuration" },
  { id: "permissions", label: "Permissions" },
  { id: "logs", label: "Logs" },
  { id: "versions", label: "Versions" },
];

const STATUS_TONE: Record<string, "default" | "success" | "warning" | "danger"> = {
  draft: "default",
  installed: "default",
  loaded: "default",
  running: "success",
  paused: "warning",
  failed: "danger",
  disabled: "warning",
  updating: "warning",
  removing: "danger",
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${SERVICE_BUILDER_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

function formatUptime(sec: number): string {
  if (!sec || sec <= 0) return "—";
  if (sec < 60) return `${Math.floor(sec)}s`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m`;
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`;
}

function DepNode({
  node,
}: {
  node: { service_id: string; status: string; state?: string | null; children?: unknown[] };
}) {
  const tone =
    node.status === "healthy"
      ? "success"
      : node.status === "missing" || node.status === "cyclic" || node.status === "failed"
        ? "danger"
        : "warning";
  return (
    <div className="ml-2 border-l border-[var(--eds-border)] pl-3">
      <div className="flex items-center gap-2 py-1">
        <span className="text-sm font-medium">{node.service_id}</span>
        <Badge tone={tone}>{node.status}</Badge>
        {node.state ? <Badge>{node.state}</Badge> : null}
      </div>
      {(node.children as Array<{ service_id: string; status: string; state?: string | null; children?: unknown[] }> | undefined)?.map(
        (child) => <DepNode key={`${node.service_id}->${child.service_id}`} node={child} />,
      )}
    </div>
  );
}

export function ServiceBuilderPage() {
  const [section, setSection] = useState<SectionId>("catalog");
  const [services, setServices] = useState<ServiceCard[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deps, setDeps] = useState<Record<string, unknown> | null>(null);
  const [health, setHealth] = useState<Array<Record<string, unknown>>>([]);
  const [logs, setLogs] = useState<Array<Record<string, unknown>>>([]);
  const [versions, setVersions] = useState<Array<Record<string, unknown>>>([]);
  const [permissions, setPermissions] = useState<Record<string, string[]> | null>(null);
  const [configText, setConfigText] = useState("{}");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("");

  const selected = useMemo(
    () => services.find((s) => s.id === selectedId) || null,
    [services, selectedId],
  );

  const refresh = useCallback(async () => {
    setError(null);
    const data = await api<{ services: ServiceCard[] }>("/services");
    setServices(data.services || []);
    if (!selectedId && data.services?.length) {
      setSelectedId(data.services[0].id);
    }
  }, [selectedId]);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  useEffect(() => {
    if (!selectedId) return;
    if (section === "dependencies") {
      api<Record<string, unknown>>(`/services/${selectedId}/dependencies`)
        .then(setDeps)
        .catch((e) => setError(String(e.message || e)));
    }
    if (section === "health") {
      api<{ services: Array<Record<string, unknown>> }>("/health")
        .then((d) => setHealth(d.services || []))
        .catch((e) => setError(String(e.message || e)));
    }
    if (section === "logs") {
      api<{ logs: Array<Record<string, unknown>> }>(`/services/${selectedId}/logs`)
        .then((d) => setLogs(d.logs || []))
        .catch((e) => setError(String(e.message || e)));
    }
    if (section === "versions") {
      api<{ versions: Array<Record<string, unknown>> }>(`/services/${selectedId}/versions`)
        .then((d) => setVersions(d.versions || []))
        .catch((e) => setError(String(e.message || e)));
    }
    if (section === "permissions") {
      api<Record<string, string[]>>(`/services/${selectedId}/permissions`)
        .then(setPermissions)
        .catch((e) => setError(String(e.message || e)));
    }
    if (section === "configuration" && selected) {
      setConfigText(JSON.stringify(selected.configuration || {}, null, 2));
    }
  }, [section, selectedId, selected]);

  async function runAction(action: string) {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      await api(`/services/${selectedId}/${action}`, { method: "POST", body: "{}" });
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  async function saveConfig() {
    if (!selectedId) return;
    setBusy(true);
    try {
      const configuration = JSON.parse(configText);
      await api(`/services/${selectedId}/configure`, {
        method: "POST",
        body: JSON.stringify({ configuration }),
      });
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    let rows = services;
    if (section === "installed") {
      rows = rows.filter((s) => !["draft", "removing"].includes(s.state));
    }
    if (section === "running") {
      rows = rows.filter((s) => s.state === "running");
    }
    if (!q) return rows;
    return rows.filter(
      (s) =>
        s.display_name.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q) ||
        s.owner.toLowerCase().includes(q),
    );
  }, [services, filter, section]);

  return (
    <PlatformBuilderLayout
      title="Enterprise Service Builder"
      subtitle="Install, version, deploy and manage platform services without modifying Core."
    >
      <div className="flex flex-wrap gap-2">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSection(s.id)}
            className={`rounded-md border px-3 py-1.5 text-xs transition ${
              section === s.id
                ? "border-[var(--eds-primary)] bg-[var(--eds-primary)]/10 text-[var(--eds-text)]"
                : "border-[var(--eds-border)] bg-[var(--eds-surface)] text-[var(--eds-text-muted)]"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {error ? (
        <Card className="border-[var(--eds-danger)]/40 bg-[var(--eds-danger)]/5 p-3 text-sm text-[var(--eds-danger)]">
          {error}
        </Card>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter services…"
          className="max-w-sm"
        />
        <Button type="button" onClick={() => refresh()} disabled={busy}>
          Refresh
        </Button>
        <Badge>{services.length} services</Badge>
      </div>

      {(section === "catalog" || section === "installed" || section === "running") && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((svc) => (
            <div
              key={svc.id}
              role="button"
              tabIndex={0}
              onClick={() => setSelectedId(svc.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") setSelectedId(svc.id);
              }}
            >
              <Card
                className={`space-y-3 p-4 ${selectedId === svc.id ? "ring-1 ring-[var(--eds-primary)]" : ""}`}
                interactive
              >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{svc.icon}</p>
                  <h3 className="eds-type-h3">{svc.display_name}</h3>
                  <p className="text-xs text-[var(--eds-text-muted)]">
                    {svc.id} · v{svc.version} · {svc.owner}
                  </p>
                </div>
                <Badge tone={STATUS_TONE[svc.state] || "default"}>{svc.state}</Badge>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs text-[var(--eds-text-muted)]">
                <div>CPU {Number(svc.cpu || 0).toFixed(1)}%</div>
                <div>RAM {Number(svc.ram || 0).toFixed(0)} MB</div>
                <div>Up {formatUptime(svc.uptime || 0)}</div>
              </div>
              <p className="text-xs text-[var(--eds-text-muted)]">
                deps: {svc.dependencies?.length ? svc.dependencies.join(", ") : "none"}
              </p>
              <div className="flex flex-wrap gap-2">
                <Button type="button" size="sm" disabled={busy} onClick={() => runAction("start")}>
                  Start
                </Button>
                <Button type="button" size="sm" disabled={busy} onClick={() => runAction("stop")}>
                  Stop
                </Button>
                <Button type="button" size="sm" disabled={busy} onClick={() => runAction("restart")}>
                  Restart
                </Button>
                <Button type="button" size="sm" disabled={busy} onClick={() => runAction("reload")}>
                  Reload
                </Button>
                <Button type="button" size="sm" disabled={busy} onClick={() => runAction("install")}>
                  Update
                </Button>
                <Button type="button" size="sm" disabled={busy} onClick={() => setSection("configuration")}>
                  Configure
                </Button>
                <Button type="button" size="sm" disabled={busy} onClick={() => setSection("logs")}>
                  Logs
                </Button>
              </div>
              </Card>
            </div>
          ))}
        </div>
      )}

      {section === "dependencies" && (
        <Card className="space-y-3 p-4">
          <h3 className="eds-type-h3">Dependency graph — {selectedId || "—"}</h3>
          {deps?.graph ? <DepNode node={deps.graph as never} /> : <p className="text-sm text-[var(--eds-text-muted)]">Select a service.</p>}
          {Array.isArray(deps?.cycles) && (deps.cycles as unknown[]).length > 0 ? (
            <Badge tone="danger">Cyclic dependencies detected</Badge>
          ) : (
            <Badge tone="success">No cycles</Badge>
          )}
          <p className="text-xs text-[var(--eds-text-muted)]">
            Startup: {Array.isArray(deps?.startup_order) ? (deps.startup_order as string[]).join(" → ") : "—"}
          </p>
        </Card>
      )}

      {section === "health" && (
        <div className="grid gap-3 md:grid-cols-2">
          {health.map((h) => (
            <Card key={String(h.service_id)} className="space-y-2 p-4">
              <div className="flex items-center justify-between">
                <h3 className="eds-type-h3">{String(h.service_id)}</h3>
                <Badge tone={h.healthy ? "success" : "danger"}>{h.healthy ? "healthy" : "unhealthy"}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-[var(--eds-text-muted)]">
                <div>Heartbeat {h.heartbeat_at ? new Date(Number(h.heartbeat_at) * 1000).toLocaleTimeString() : "—"}</div>
                <div>Response {Number(h.response_time_ms || 0).toFixed(1)} ms</div>
                <div>Memory {Number(h.memory_mb || 0).toFixed(0)} MB</div>
                <div>CPU {Number(h.cpu_pct || 0).toFixed(1)}%</div>
                <div>Errors {String(h.errors ?? 0)}</div>
                <div>Restarts {String(h.restart_count ?? 0)}</div>
                <div>Availability {Number(h.availability_pct || 0).toFixed(1)}%</div>
                <div>Status {String(h.status)}</div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {section === "configuration" && selected && (
        <Card className="space-y-3 p-4">
          <h3 className="eds-type-h3">Configuration — {selected.display_name}</h3>
          <textarea
            className="min-h-[220px] w-full rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] p-3 font-mono text-xs"
            value={configText}
            onChange={(e) => setConfigText(e.target.value)}
          />
          <Button type="button" disabled={busy} onClick={saveConfig}>
            Save configuration
          </Button>
        </Card>
      )}

      {section === "permissions" && (
        <Card className="space-y-3 p-4">
          <h3 className="eds-type-h3">Permissions — {selectedId || "—"}</h3>
          {permissions ? (
            <div className="grid gap-3 md:grid-cols-2">
              {Object.entries(permissions).map(([key, values]) => (
                <div key={key}>
                  <p className="text-xs font-medium uppercase text-[var(--eds-text-muted)]">{key}</p>
                  <ul className="mt-1 space-y-1 text-sm">
                    {(values || []).map((v) => (
                      <li key={v}>{v}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--eds-text-muted)]">No permissions loaded.</p>
          )}
        </Card>
      )}

      {section === "logs" && (
        <Card className="space-y-2 p-4">
          <h3 className="eds-type-h3">Logs — {selectedId || "—"}</h3>
          <div className="max-h-[420px] space-y-2 overflow-auto">
            {logs.length === 0 ? (
              <p className="text-sm text-[var(--eds-text-muted)]">No audit entries yet.</p>
            ) : (
              logs
                .slice()
                .reverse()
                .map((log) => (
                  <div key={String(log.log_id)} className="border-b border-[var(--eds-border)] py-2 text-xs">
                    <div className="flex flex-wrap gap-2">
                      <Badge>{String(log.operation || log.level)}</Badge>
                      <span>{String(log.actor)}</span>
                      <span>
                        {String(log.old_state || "—")} → {String(log.new_state || "—")}
                      </span>
                      <Badge tone={log.result === "ok" ? "success" : "danger"}>{String(log.result)}</Badge>
                      {log.duration_ms != null ? <span>{Number(log.duration_ms).toFixed(1)} ms</span> : null}
                    </div>
                    <p className="mt-1 text-[var(--eds-text-muted)]">{String(log.message)}</p>
                  </div>
                ))
            )}
          </div>
        </Card>
      )}

      {section === "versions" && (
        <Card className="space-y-2 p-4">
          <h3 className="eds-type-h3">Versions — {selectedId || "—"}</h3>
          {versions.map((v) => (
            <div key={`${v.service_id}-${v.version}`} className="flex items-center justify-between border-b border-[var(--eds-border)] py-2 text-sm">
              <div>
                <p className="font-medium">v{String(v.version)}</p>
                <p className="text-xs text-[var(--eds-text-muted)]">{String(v.changelog || "")}</p>
              </div>
              {v.is_active ? <Badge tone="success">active</Badge> : <Badge>history</Badge>}
            </div>
          ))}
        </Card>
      )}
    </PlatformBuilderLayout>
  );
}

export default ServiceBuilderPage;
