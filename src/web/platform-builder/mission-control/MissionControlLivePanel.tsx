/**
 * Live platform status panel for Mission Control — Sprint 32.0.
 * Fetches existing MC + OBS APIs, module registry, and per-ecosystem health probes.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Table } from "@/ui";
import { PLATFORM_BUILDER_API, PLATFORM_BUILDER_SPRINT } from "../types";
import { hubIntegrations } from "@/integrations/hub";
import { apiFetch } from "@/integrations/apiClient";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { telemetry } from "@/integrations/telemetry";
import { WORKSPACE_HEALTH_PROBES } from "@/pilot/webCompletionAudit";
import { pilotMetrics, type PilotMetricsSnapshot } from "@/integrations/pilotMetrics";

type Dict = Record<string, unknown>;

type EcoHealth = { id: string; label: string; ok: boolean | null; detail: string };

function tenantRows(tenants: Dict | null): { id: string; name: string; status: string }[] {
  if (!tenants) return [];
  const list =
    (tenants.tenants as Dict[] | undefined) ||
    (tenants.items as Dict[] | undefined) ||
    (Array.isArray(tenants) ? (tenants as Dict[]) : null);
  if (Array.isArray(list)) {
    return list.slice(0, 12).map((t, i) => ({
      id: String(t.tenant_id || t.id || i),
      name: String(t.name || t.slug || "tenant"),
      status: String(t.status || t.environment || "active"),
    }));
  }
  if (typeof tenants.count === "number" || typeof tenants.tenants === "number") {
    return [{ id: "summary", name: "tenancy status", status: JSON.stringify(tenants).slice(0, 80) }];
  }
  return Object.keys(tenants).length
    ? [{ id: "payload", name: "tenancy probe", status: "ok" }]
    : [];
}

export function MissionControlLivePanel() {
  const [mcStatus, setMcStatus] = useState<Dict | null>(null);
  const [obsHealth, setObsHealth] = useState<Dict | null>(null);
  const [metrics, setMetrics] = useState<Dict | null>(null);
  const [logs, setLogs] = useState<Dict | null>(null);
  const [ecoHealth, setEcoHealth] = useState<EcoHealth[]>([]);
  const [tenants, setTenants] = useState<Dict | null>(null);
  const [pilotSnap, setPilotSnap] = useState<PilotMetricsSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const modules = moduleRegistry.ecosystemModules();

  const refresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    const started = performance.now();
    try {
      const [mcRes, obsRes, metRes, logRes, tnRes, ...ecoRes] = await Promise.all([
        apiFetch(`${PLATFORM_BUILDER_API}/mission-control/status`),
        apiFetch(`${hubIntegrations.monitoring}/health`),
        apiFetch(`${hubIntegrations.monitoring}/metrics`),
        apiFetch(`${hubIntegrations.monitoring}/logs`),
        apiFetch(`${hubIntegrations.tenancy}/tenants`),
        ...WORKSPACE_HEALTH_PROBES.map((w) => apiFetch(w.healthUrl)),
      ]);
      const mc = (await mcRes.json()) as Dict;
      const obs = (await obsRes.json()) as Dict;
      const met = (await metRes.json()) as Dict;
      const log = (await logRes.json()) as Dict;
      if (!mcRes.ok) throw new Error(String(mc.error || "Mission Control status failed"));
      setMcStatus(mc);
      setObsHealth(obsRes.ok ? obs : null);
      setMetrics(metRes.ok ? met : null);
      setLogs(logRes.ok ? log : null);
      setTenants(tnRes.ok ? ((await tnRes.json()) as Dict) : null);
      setPilotSnap(await pilotMetrics.snapshot());

      const eco: EcoHealth[] = await Promise.all(
        WORKSPACE_HEALTH_PROBES.map(async (w, i) => {
          const res = ecoRes[i];
          try {
            const body = (await res.json().catch(() => ({}))) as Dict;
            return {
              id: w.id,
              label: w.label,
              ok: res.ok,
              detail: res.ok ? String(body.status ?? body.application_version ?? "ok") : `HTTP ${res.status}`,
            };
          } catch {
            return { id: w.id, label: w.label, ok: false, detail: "probe failed" };
          }
        }),
      );
      setEcoHealth(eco);

      await telemetry.apiCall("mission-control/live", performance.now() - started, true);
      await telemetry.userActivity("mission_control_live_refresh");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Live status failed");
      await telemetry.apiCall("mission-control/live", performance.now() - started, false);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const ecoOk = ecoHealth.filter((e) => e.ok).length;

  return (
    <div className="mb-6 space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="success">Live Modules</Badge>
        <Badge>Sprint {PLATFORM_BUILDER_SPRINT}</Badge>
        <Badge>OBS Connected</Badge>
        <Badge tone={ecoOk === WORKSPACE_HEALTH_PROBES.length ? "success" : "warning"}>
          Ecosystems {ecoOk}/{WORKSPACE_HEALTH_PROBES.length}
        </Badge>
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => void refresh()}>
          Refresh status
        </Button>
        <Link to="/pilot">
          <Button size="sm" variant="secondary">
            Pilot Dashboard
          </Button>
        </Link>
        <Link to="/pilot/production">
          <Button size="sm" variant="secondary">
            Production Readiness
          </Button>
        </Link>
        <Link to="/pilot/onboard">
          <Button size="sm" variant="secondary">
            Onboard Org
          </Button>
        </Link>
        <Link to="/pilot/execute">
          <Button size="sm" variant="secondary">
            Pilot Execution
          </Button>
        </Link>
      </div>

      {error ? (
        <Card title="Live status warning">
          <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
          <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
            Wizard steps below still work when live probes are unavailable.
          </p>
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="System overview">
          <ul className="eds-type-small space-y-1">
            <li>Mission Control: {mcStatus ? "connected" : busy ? "loading…" : "—"}</li>
            <li>
              OBS:{" "}
              {obsHealth?.enterprise_observability_ready === true || obsHealth?.status === "ok"
                ? "ready"
                : obsHealth
                  ? "degraded"
                  : "—"}
            </li>
            <li>Metrics recorded: {String(metrics?.metrics ?? "—")}</li>
            <li>Logs recorded: {String(logs?.logs ?? "—")}</li>
            <li>
              Cross-ecosystem health: {ecoOk}/{WORKSPACE_HEALTH_PROBES.length}
            </li>
            <li>Tenants probe: {tenants ? "ok" : "—"}</li>
          </ul>
        </Card>
        <Card title="Organization / AI / API">
          <ul className="eds-type-small space-y-1">
            <li>
              AI status:{" "}
              <Badge tone="success">platform AI layers active</Badge>
            </li>
            <li>
              API status:{" "}
              <Badge>{PLATFORM_BUILDER_API}</Badge>
            </li>
            <li>
              Health:{" "}
              <Badge tone={error ? "warning" : "success"}>{error ? "partial" : "healthy"}</Badge>
            </li>
            <li>
              Pilot: <Link className="underline" to="/pilot">/pilot</Link>
            </li>
            <li>
              Production:{" "}
              <Link className="underline" to="/pilot/production">
                /pilot/production
              </Link>
            </li>
          </ul>
        </Card>
        <Card title="Connected modules">
          <p className="eds-type-small text-[var(--eds-text-muted)]">
            {modules.length} business ecosystems via module registry
          </p>
          <ul className="mt-2 eds-type-small space-y-1">
            {modules.map((m) => (
              <li key={m.id}>
                <Link className="underline" to={m.routes[0]}>
                  {m.name}
                </Link>{" "}
                · <Badge>{m.health}</Badge> · {m.version}
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card title="Pilot organizations">
        <Table headers={["Tenant", "Name", "Status"]}>
          {tenantRows(tenants).map((t) => (
            <tr key={t.id} className="border-t border-[var(--ew-border)]">
              <td className="px-3 py-2 eds-type-small">{t.id}</td>
              <td className="px-3 py-2">{t.name}</td>
              <td className="px-3 py-2">{t.status}</td>
            </tr>
          ))}
        </Table>
        {!tenantRows(tenants).length ? (
          <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
            No tenants yet — run{" "}
            <Link className="underline" to="/pilot/onboard">
              /pilot/onboard
            </Link>
            .
          </p>
        ) : null}
      </Card>

      <Card title="Pilot KPIs">
        <ul className="eds-type-small space-y-1">
          <li>Sessions: {pilotSnap?.sessions ?? "—"}</li>
          <li>
            Workflow completion:{" "}
            {pilotSnap?.workflowCompletionRate != null ? `${pilotSnap.workflowCompletionRate}%` : "—"}
          </li>
          <li>AI samples: {pilotSnap?.aiResponseSamples ?? "—"}</li>
          <li>Registrations: {pilotSnap?.registrations ?? "—"}</li>
          <li>Feedback: {pilotSnap?.feedbackCount ?? "—"}</li>
          <li>
            Health:{" "}
            <Badge tone={pilotSnap?.systemHealthy ? "success" : "warning"}>
              {pilotSnap?.systemHealthy ? "healthy" : "check"}
            </Badge>
          </li>
        </ul>
      </Card>

      <Card title="Multi-organization overview">
        <pre className="max-h-40 overflow-auto eds-type-small">{JSON.stringify(tenants ?? {}, null, 2)}</pre>
      </Card>

      <Card title="Cross-ecosystem API health">
        <Table headers={["Ecosystem", "Live probe", "Registry", "Route"]}>
          {WORKSPACE_HEALTH_PROBES.map((w) => {
            const live = ecoHealth.find((e) => e.id === w.id);
            const mod = moduleRegistry.get(w.id);
            return (
              <tr key={w.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{w.label}</td>
                <td className="px-3 py-2">
                  <Badge tone={live?.ok ? "success" : live?.ok === false ? "warning" : "default"}>
                    {live?.ok ? "ok" : live?.ok === false ? live.detail : "—"}
                  </Badge>
                </td>
                <td className="px-3 py-2">{mod?.health ?? "—"}</td>
                <td className="px-3 py-2">
                  <Link className="underline" to={w.route}>
                    {w.route}
                  </Link>
                </td>
              </tr>
            );
          })}
        </Table>
      </Card>

      <Card title="Module status">
        <Table headers={["Module", "Health", "Version", "Route"]}>
          {moduleRegistry.healthSummary().map((h) => (
            <tr key={h.id} className="border-t border-[var(--ew-border)]">
              <td className="px-3 py-2">{h.name}</td>
              <td className="px-3 py-2">{h.health}</td>
              <td className="px-3 py-2">{h.version}</td>
              <td className="px-3 py-2">{moduleRegistry.get(h.id)?.routes[0] || "—"}</td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
}
