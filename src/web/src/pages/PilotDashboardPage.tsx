/**
 * Pilot Dashboard — Sprint 30.5.
 * First internal pilot readiness surface. Reuses shell + EDS + OBS + module registry.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Badge,
  Button,
  Card,
  Charts,
  Table,
  NotificationsPanel,
} from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useWebCore } from "@/shell/WebCoreProvider";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { sharedUiChecklist } from "@/ui/sharedUi";
import { hubIntegrations } from "@/integrations/hub";
import { apiFetch } from "@/integrations/apiClient";
import { telemetry } from "@/integrations/telemetry";
import { PLATFORM_BUILDER_API, PLATFORM_BUILDER_VERSION } from "../../platform-builder/types";
import { webConfig } from "@/config/webConfig";

type Dict = Record<string, unknown>;

export function PilotDashboardPage() {
  const core = useWebCore();
  const [obsHealth, setObsHealth] = useState<Dict | null>(null);
  const [metrics, setMetrics] = useState<Dict | null>(null);
  const [logs, setLogs] = useState<Dict | null>(null);
  const [platformDash, setPlatformDash] = useState<Dict | null>(null);
  const [mcStatus, setMcStatus] = useState<Dict | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [apiCalls, setApiCalls] = useState(0);

  const refresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [obsRes, metRes, logRes, dashRes, mcRes] = await Promise.all([
        apiFetch(`${hubIntegrations.monitoring}/health`),
        apiFetch(`${hubIntegrations.monitoring}/metrics`),
        apiFetch(`${hubIntegrations.monitoring}/logs`),
        apiFetch(`${hubIntegrations.monitoring}/dashboard`, {
          method: "POST",
          body: JSON.stringify({ dashboard_type: "platform" }),
        }),
        apiFetch(`${PLATFORM_BUILDER_API}/mission-control/status`),
      ]);
      setApiCalls(5);
      setObsHealth(obsRes.ok ? ((await obsRes.json()) as Dict) : null);
      setMetrics(metRes.ok ? ((await metRes.json()) as Dict) : null);
      setLogs(logRes.ok ? ((await logRes.json()) as Dict) : null);
      setPlatformDash(dashRes.ok ? ((await dashRes.json()) as Dict) : null);
      setMcStatus(mcRes.ok ? ((await mcRes.json()) as Dict) : null);
      if (!obsRes.ok && !mcRes.ok) {
        setError("Observability and Mission Control probes failed — check API connectivity.");
      }
      await telemetry.audit("pilot_dashboard_refresh", core.tenantId || "demo");
      await telemetry.userActivity("pilot_dashboard_view");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Pilot refresh failed");
      await telemetry.error("pilot_dashboard_refresh", e instanceof Error ? e : undefined);
    } finally {
      setBusy(false);
    }
  }, [core.tenantId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const ecosystems = moduleRegistry.ecosystemModules();
  const healthRows = moduleRegistry.healthSummary();
  const metricCount = Number(metrics?.metrics ?? 0);
  const logCount = Number(logs?.logs ?? 0);
  const chartValues = [
    core.modulesHealthy,
    ecosystems.length,
    metricCount,
    logCount,
    apiCalls,
  ];

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">Pilot Dashboard</Badge>
        <Badge>Sprint 30.5</Badge>
        <Badge>PB {PLATFORM_BUILDER_VERSION}</Badge>
        <Badge>{webConfig.sprint}</Badge>
        {core.ecosystemsReady ? <Badge tone="success">7 ecosystems registered</Badge> : null}
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">First Pilot Readiness</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Live view of platform status, connected modules, and OBS telemetry for the first internal
        pilot. Uses the shared application shell — not a parallel dashboard stack.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" disabled={busy} onClick={() => void refresh()}>
          Refresh telemetry
        </Button>
        <Link to="/platform-builder/mission-control">
          <Button size="sm" variant="secondary">
            Mission Control
          </Button>
        </Link>
        <Link to="/workspace/auto">
          <Button size="sm" variant="secondary">
            Automotive module
          </Button>
        </Link>
      </div>

      {error ? (
        <div className="mt-4">
          <EmptyState
            title="Telemetry warning"
            description={error}
            actionLabel="Open Mission Control"
            actionTo="/platform-builder/mission-control"
          />
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card title="Platform status">
          <ul className="eds-type-small space-y-1">
            <li>
              Web Core: <Badge tone={core.ready ? "success" : "warning"}>{core.ready ? "ready" : "booting"}</Badge>
            </li>
            <li>
              Org: {core.organization} · {core.department}
            </li>
            <li>
              User: {core.email || "—"} · {core.roleId || "—"}
            </li>
            <li>
              Modules healthy: {core.modulesHealthy}/{core.modulesTotal}
            </li>
            <li>
              MC probe: {mcStatus ? "ok" : "—"}
            </li>
            <li>
              OBS:{" "}
              {obsHealth?.status === "ok" || obsHealth?.enterprise_observability_ready
                ? "ready"
                : "—"}
            </li>
          </ul>
        </Card>

        <Card title="Connected modules">
          <ul className="eds-type-small space-y-1">
            {ecosystems.map((m) => (
              <li key={m.id}>
                <Link className="underline" to={m.routes[0]}>
                  {m.name}
                </Link>{" "}
                · <Badge>{m.health}</Badge>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="User sessions / context">
          <ul className="eds-type-small space-y-1">
            <li>Tenant: {core.tenantId || "—"}</li>
            <li>Project: {core.project}</li>
            <li>Theme: {core.themeMode}</li>
            <li>Permissions: {core.permissions.join(", ") || "—"}</li>
            <li>Nav items: {core.navigation.length}</li>
            <li>Telemetry: {webConfig.telemetryEnabled ? "enabled" : "disabled"}</li>
          </ul>
        </Card>

        <Card title="Performance / API calls">
          <Charts
            labels={["Healthy mods", "Ecosystems", "Metrics", "Logs", "API probes"]}
            values={chartValues}
          />
          <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
            Last refresh probed {apiCalls} endpoints.
          </p>
        </Card>

        <Card title="Errors / warnings">
          {error ? (
            <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">No client errors this session.</p>
          )}
          <p className="mt-2 eds-type-small">OBS error logs counted in business dashboard render.</p>
        </Card>

        <Card title="AI / business events">
          <ul className="eds-type-small space-y-1">
            <li>
              AI activity: use telemetry.aiActivity from modules (OBS kind=ai)
            </li>
            <li>
              Business metrics: {String((platformDash?.metrics as Dict)?.alerts ?? "via OBS dashboard")}
            </li>
            <li>
              Platform dash id: {String(platformDash?.dashboard_id ?? "—")}
            </li>
          </ul>
        </Card>

        <Card title="Notifications">
          <NotificationsPanel />
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Module registry health">
          <Table headers={["Name", "Kind", "Health", "Version"]}>
            {healthRows.map((h) => (
              <tr key={h.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{h.name}</td>
                <td className="px-3 py-2">{h.kind}</td>
                <td className="px-3 py-2">{h.health}</td>
                <td className="px-3 py-2">{h.version}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Shared UI connected">
          <ul className="eds-type-small columns-2 gap-4 space-y-1">
            {sharedUiChecklist().map((g) => (
              <li key={g.group}>
                <strong>{g.group}</strong>: {g.components.join(", ")}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
