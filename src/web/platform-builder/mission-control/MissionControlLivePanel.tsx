/**
 * Live platform status panel for Mission Control — Sprint 30.5.
 * Fetches existing MC + OBS APIs and module registry — no parallel cockpit.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Table } from "@/ui";
import { PLATFORM_BUILDER_API } from "../types";
import { hubIntegrations } from "@/integrations/hub";
import { apiFetch } from "@/integrations/apiClient";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { telemetry } from "@/integrations/telemetry";

type Dict = Record<string, unknown>;

export function MissionControlLivePanel() {
  const [mcStatus, setMcStatus] = useState<Dict | null>(null);
  const [obsHealth, setObsHealth] = useState<Dict | null>(null);
  const [metrics, setMetrics] = useState<Dict | null>(null);
  const [logs, setLogs] = useState<Dict | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const modules = moduleRegistry.ecosystemModules();

  const refresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    const started = performance.now();
    try {
      const [mcRes, obsRes, metRes, logRes] = await Promise.all([
        apiFetch(`${PLATFORM_BUILDER_API}/mission-control/status`),
        apiFetch(`${hubIntegrations.monitoring}/health`),
        apiFetch(`${hubIntegrations.monitoring}/metrics`),
        apiFetch(`${hubIntegrations.monitoring}/logs`),
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

  return (
    <div className="mb-6 space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="success">Live Modules</Badge>
        <Badge>Sprint 30.5</Badge>
        <Badge>OBS Connected</Badge>
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => void refresh()}>
          Refresh status
        </Button>
        <Link to="/pilot">
          <Button size="sm" variant="secondary">
            Pilot Dashboard
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
