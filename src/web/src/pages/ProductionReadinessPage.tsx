/**
 * Production Readiness — Sprint 32.0.
 * Surfaces existing EPD / EPR / OBS / MC / workspace health probes — no new engines.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Table } from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { hubIntegrations } from "@/integrations/hub";
import { apiFetch } from "@/integrations/apiClient";
import { telemetry } from "@/integrations/telemetry";
import { sharedUiChecklist } from "@/ui/sharedUi";
import { PLATFORM_BUILDER_VERSION } from "../../platform-builder/types";
import { webConfig } from "@/config/webConfig";
import {
  PILOT_OPS_STEPS,
  PLATFORM_HEALTH_PROBES,
  PRODUCTION_CHECKLIST,
  WORKSPACE_HEALTH_PROBES,
  productionReadinessScore,
  webCompletionSummary,
} from "../pilot/webCompletionAudit";

type ProbeRow = {
  id: string;
  label: string;
  url: string;
  ok: boolean | null;
  detail: string;
};

type Dict = Record<string, unknown>;

export function ProductionReadinessPage() {
  const [workspaceRows, setWorkspaceRows] = useState<ProbeRow[]>([]);
  const [platformRows, setPlatformRows] = useState<ProbeRow[]>([]);
  const [epdHealth, setEpdHealth] = useState<Dict | null>(null);
  const [epdDash, setEpdDash] = useState<Dict | null>(null);
  const [gateResult, setGateResult] = useState<Dict | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const score = productionReadinessScore();
  const summary = webCompletionSummary();

  const refresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    const started = performance.now();
    try {
      const wsProbes = await Promise.all(
        WORKSPACE_HEALTH_PROBES.map(async (w) => {
          try {
            const res = await apiFetch(w.healthUrl);
            const body = (await res.json().catch(() => ({}))) as Dict;
            return {
              id: w.id,
              label: w.label,
              url: w.healthUrl,
              ok: res.ok,
              detail: res.ok
                ? String(body.status ?? body.application_version ?? "ok")
                : `HTTP ${res.status}`,
            } satisfies ProbeRow;
          } catch (e) {
            return {
              id: w.id,
              label: w.label,
              url: w.healthUrl,
              ok: false,
              detail: e instanceof Error ? e.message : "probe failed",
            } satisfies ProbeRow;
          }
        }),
      );
      setWorkspaceRows(wsProbes);

      const platProbes = await Promise.all(
        PLATFORM_HEALTH_PROBES.map(async (p) => {
          try {
            const res = await apiFetch(p.healthUrl);
            const body = (await res.json().catch(() => ({}))) as Dict;
            return {
              id: p.id,
              label: p.label,
              url: p.healthUrl,
              ok: res.ok,
              detail: res.ok
                ? String(body.status ?? body.production_platform_ready ?? "ok")
                : `HTTP ${res.status}`,
            } satisfies ProbeRow;
          } catch (e) {
            return {
              id: p.id,
              label: p.label,
              url: p.healthUrl,
              ok: false,
              detail: e instanceof Error ? e.message : "probe failed",
            } satisfies ProbeRow;
          }
        }),
      );
      setPlatformRows(platProbes);

      const [healthRes, dashRes] = await Promise.all([
        apiFetch(`${hubIntegrations.productionReadiness}/health`),
        apiFetch(`${hubIntegrations.productionReadiness}/dashboard`),
      ]);
      setEpdHealth(healthRes.ok ? ((await healthRes.json()) as Dict) : null);
      setEpdDash(dashRes.ok ? ((await dashRes.json()) as Dict) : null);

      if (!healthRes.ok && wsProbes.every((r) => !r.ok)) {
        setError("Production readiness probes unavailable — check API connectivity.");
      }
      await telemetry.apiCall("production-readiness/refresh", performance.now() - started, true);
      await telemetry.userActivity("production_readiness_view");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Production readiness refresh failed");
      await telemetry.apiCall("production-readiness/refresh", performance.now() - started, false);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function runGate() {
    setBusy(true);
    try {
      const res = await apiFetch(`${hubIntegrations.productionReadiness}/gate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ release: webConfig.version }),
      });
      const body = (await res.json()) as Dict;
      setGateResult(body);
      if (!res.ok) setError(String(body.error || `Gate HTTP ${res.status}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gate failed");
    } finally {
      setBusy(false);
    }
  }

  const wsOk = workspaceRows.filter((r) => r.ok).length;
  const platOk = platformRows.filter((r) => r.ok).length;

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">Enterprise Web Completion</Badge>
        <Badge>Sprint 32.0</Badge>
        <Badge>PB {PLATFORM_BUILDER_VERSION}</Badge>
        <Badge tone={score >= 80 ? "success" : "warning"}>Score {score}</Badge>
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">Production Readiness</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Validates the completed seven-ecosystem Enterprise Platform for external pilot preparation.
        Reuses EPD, EPR, OBS, and Mission Control — no duplicated stacks.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" disabled={busy} onClick={() => void refresh()}>
          {busy ? "Probing…" : "Refresh probes"}
        </Button>
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => void runGate()}>
          Run EPD gate
        </Button>
        <Link to="/pilot">
          <Button size="sm" variant="secondary">
            Pilot Dashboard
          </Button>
        </Link>
        <Link to="/platform-builder/mission-control">
          <Button size="sm" variant="secondary">
            Mission Control
          </Button>
        </Link>
      </div>

      {error ? (
        <div className="mt-4">
          <EmptyState title="Probe warning" description={error} actionLabel="Open Pilot" actionTo="/pilot" />
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card title="Platform health">
          <ul className="eds-type-small space-y-1">
            <li>
              Workspaces: {wsOk}/{summary.ecosystems || WORKSPACE_HEALTH_PROBES.length}
            </li>
            <li>
              Platform probes: {platOk}/{PLATFORM_HEALTH_PROBES.length}
            </li>
            <li>
              EPD:{" "}
              {epdHealth?.production_platform_ready === true || epdHealth?.status === "ok"
                ? "ready"
                : epdHealth
                  ? "partial"
                  : "—"}
            </li>
            <li>Checklist ready: {summary.readyCount}/{summary.productionItems}</li>
          </ul>
        </Card>
        <Card title="Readiness score">
          <p className="eds-type-title">{score}%</p>
          <p className="mt-1 eds-type-small text-[var(--eds-text-muted)]">
            Weighted from auth, RBAC, gateway, OBS, backups, secrets, and known gaps.
          </p>
        </Card>
        <Card title="EPD suite">
          <pre className="max-h-36 overflow-auto eds-type-small">
            {JSON.stringify(epdHealth?.suite ?? epdHealth ?? {}, null, 2)}
          </pre>
        </Card>
        <Card title="EPD dashboard">
          <pre className="max-h-36 overflow-auto eds-type-small">
            {JSON.stringify(epdDash ?? {}, null, 2)}
          </pre>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="Workspace health (7 ecosystems)">
          <Table headers={["Workspace", "Probe", "Status", "Detail"]}>
            {workspaceRows.map((r) => (
              <tr key={r.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">
                  <Link className="underline" to={WORKSPACE_HEALTH_PROBES.find((w) => w.id === r.id)!.route}>
                    {r.label}
                  </Link>
                </td>
                <td className="px-3 py-2 eds-type-small">{r.url}</td>
                <td className="px-3 py-2">
                  <Badge tone={r.ok ? "success" : r.ok === false ? "warning" : "default"}>
                    {r.ok ? "ok" : r.ok === false ? "fail" : "—"}
                  </Badge>
                </td>
                <td className="px-3 py-2 eds-type-small">{r.detail}</td>
              </tr>
            ))}
          </Table>
        </Card>

        <Card title="Platform probes">
          <Table headers={["Surface", "Probe", "Status", "Detail"]}>
            {platformRows.map((r) => (
              <tr key={r.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{r.label}</td>
                <td className="px-3 py-2 eds-type-small">{r.url}</td>
                <td className="px-3 py-2">
                  <Badge tone={r.ok ? "success" : r.ok === false ? "warning" : "default"}>
                    {r.ok ? "ok" : r.ok === false ? "fail" : "—"}
                  </Badge>
                </td>
                <td className="px-3 py-2 eds-type-small">{r.detail}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="Production checklist">
          <Table headers={["Item", "Status"]}>
            {PRODUCTION_CHECKLIST.map((c) => (
              <tr key={c.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{c.label}</td>
                <td className="px-3 py-2">
                  <Badge
                    tone={c.status === "ready" ? "success" : c.status === "partial" ? "warning" : "danger"}
                  >
                    {c.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </Table>
        </Card>

        <Card title="Pilot operations">
          <Table headers={["Step", "Route", "Note"]}>
            {PILOT_OPS_STEPS.map((s) => (
              <tr key={s.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{s.label}</td>
                <td className="px-3 py-2">
                  <Link className="underline" to={s.route}>
                    {s.route}
                  </Link>
                </td>
                <td className="px-3 py-2 eds-type-small text-[var(--eds-text-muted)]">
                  {"note" in s ? s.note : "—"}
                </td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="Shared UI inventory">
          <ul className="eds-type-small space-y-1">
            {sharedUiChecklist().map((g) => (
              <li key={g.group}>
                <Badge>{g.group}</Badge> {g.components.join(", ")}
              </li>
            ))}
          </ul>
        </Card>
        <Card title="EPD gate result">
          {gateResult ? (
            <pre className="max-h-48 overflow-auto eds-type-small">{JSON.stringify(gateResult, null, 2)}</pre>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              Run the existing EPD gate against release {webConfig.version}.
            </p>
          )}
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
