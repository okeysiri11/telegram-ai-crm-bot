/**
 * Pilot Dashboard — Sprint 30.5 / hardened 30.7.
 * Operational metrics, role journeys, central feedback, business OBS dashboards.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Badge,
  Button,
  Card,
  Charts,
  Input,
  Select,
  Table,
  NotificationsPanel,
} from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useWebCore } from "@/shell/WebCoreProvider";
import { useAuthStore } from "@/auth/authStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";
import { sharedUiChecklist } from "@/ui/sharedUi";
import { hubIntegrations } from "@/integrations/hub";
import { apiFetch } from "@/integrations/apiClient";
import { telemetry } from "@/integrations/telemetry";
import {
  listLocalFeedback,
  submitPilotFeedback,
  type FeedbackCategory,
  type PilotFeedbackRecord,
} from "@/integrations/pilotFeedback";
import { pilotMetrics, type PilotMetricsSnapshot } from "@/integrations/pilotMetrics";
import { validateJourneys } from "../pilot/roleJourneys";
import {
  WORKSPACE_HEALTH_PROBES,
  productionReadinessScore,
  webCompletionSummary,
} from "../pilot/webCompletionAudit";
import { PLATFORM_BUILDER_API, PLATFORM_BUILDER_VERSION } from "../../platform-builder/types";
import { webConfig } from "@/config/webConfig";
import { isJwtToken } from "@/auth/identityApi";

type Dict = Record<string, unknown>;

export function PilotDashboardPage() {
  const core = useWebCore();
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const authMode = useAuthStore((s) => s.authMode);
  const pushNotif = useNotificationStore((s) => s.push);

  const [obsHealth, setObsHealth] = useState<Dict | null>(null);
  const [metrics, setMetrics] = useState<Dict | null>(null);
  const [logs, setLogs] = useState<Dict | null>(null);
  const [mcStatus, setMcStatus] = useState<Dict | null>(null);
  const [epdHealth, setEpdHealth] = useState<Dict | null>(null);
  const [eprHealth, setEprHealth] = useState<Dict | null>(null);
  const [pilotSnap, setPilotSnap] = useState<PilotMetricsSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [apiCalls, setApiCalls] = useState(0);
  const readinessScore = productionReadinessScore();
  const webSummary = webCompletionSummary();

  const [fbCategory, setFbCategory] = useState<FeedbackCategory>("suggestion");
  const [fbMessage, setFbMessage] = useState("");
  const [fbFeature, setFbFeature] = useState("automotive");
  const [fbBusy, setFbBusy] = useState(false);
  const [feedbackItems, setFeedbackItems] = useState<PilotFeedbackRecord[]>(() => listLocalFeedback());

  const journeys = useMemo(
    () =>
      validateJourneys({
        authenticated: Boolean(user),
        roleId: user?.roleId,
        roles: user?.roles,
      }),
    [user],
  );

  const refresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [obsRes, metRes, logRes, mcRes, epdRes, eprRes, snap] = await Promise.all([
        apiFetch(`${hubIntegrations.monitoring}/health`),
        apiFetch(`${hubIntegrations.monitoring}/metrics`),
        apiFetch(`${hubIntegrations.monitoring}/logs`),
        apiFetch(`${PLATFORM_BUILDER_API}/mission-control/status`),
        apiFetch(`${hubIntegrations.productionReadiness}/health`),
        apiFetch(`${hubIntegrations.pilotReadiness}/health`),
        pilotMetrics.snapshot(),
      ]);
      setApiCalls(8);
      setObsHealth(obsRes.ok ? ((await obsRes.json()) as Dict) : null);
      setMetrics(metRes.ok ? ((await metRes.json()) as Dict) : null);
      setLogs(logRes.ok ? ((await logRes.json()) as Dict) : null);
      setMcStatus(mcRes.ok ? ((await mcRes.json()) as Dict) : null);
      setEpdHealth(epdRes.ok ? ((await epdRes.json()) as Dict) : null);
      setEprHealth(eprRes.ok ? ((await eprRes.json()) as Dict) : null);
      setPilotSnap(snap);
      setFeedbackItems(listLocalFeedback());
      if (!obsRes.ok && !mcRes.ok) {
        setError("Observability and Mission Control probes failed — check API connectivity.");
      }
      await telemetry.audit("pilot_dashboard_refresh", core.tenantId || "demo");
      await telemetry.userActivity("pilot_dashboard_view");
      pilotMetrics.recordSession();
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

  async function onSubmitFeedback() {
    if (!fbMessage.trim()) return;
    setFbBusy(true);
    try {
      const record = await submitPilotFeedback({
        category: fbCategory,
        message: fbMessage.trim(),
        feature: fbFeature,
      });
      setFeedbackItems(listLocalFeedback());
      setFbMessage("");
      pushNotif({
        kind: "alert",
        title: `Feedback ${record.severity}`,
        body: `Trace ${record.trace_id} → module ${record.module}`,
      });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Feedback failed");
    } finally {
      setFbBusy(false);
    }
  }

  const ecosystems = moduleRegistry.ecosystemModules();
  const healthRows = moduleRegistry.healthSummary();
  const metricCount = Number(metrics?.metrics ?? 0);
  const logCount = Number(logs?.logs ?? 0);
  const chartValues = [
    pilotSnap?.sessions ?? 0,
    pilotSnap?.workflowCompletionRate ?? 0,
    pilotSnap?.avgProcessingMs ?? 0,
    metricCount,
    logCount,
    apiCalls,
  ];

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">Enterprise Web Completion</Badge>
        <Badge>Sprint 32.0</Badge>
        <Badge>PB {PLATFORM_BUILDER_VERSION}</Badge>
        <Badge>{webConfig.sprint}</Badge>
        <Badge tone={readinessScore >= 80 ? "success" : "warning"}>Ready {readinessScore}%</Badge>
        {isJwtToken(accessToken) ? <Badge tone="success">JWT</Badge> : <Badge>{authMode || "ISAM"}</Badge>}
        {core.ecosystemsReady ? <Badge tone="success">7 ecosystems</Badge> : null}
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">
        Pilot Operations — Auto · Beauty · Cafe · Agriculture · Legal · Bidex · Drone
      </h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Unified pilot operations across seven ecosystems on one Enterprise Platform. Production readiness
        probes EPD/EPR/OBS — no new ecosystems, no duplicated stacks.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" disabled={busy} onClick={() => void refresh()}>
          Refresh metrics
        </Button>
        <Link to="/workspace/auto">
          <Button size="sm" variant="secondary">
            Automotive
          </Button>
        </Link>
        <Link to="/workspace/beauty">
          <Button size="sm" variant="secondary">
            Beauty
          </Button>
        </Link>
        <Link to="/workspace/cafe">
          <Button size="sm" variant="secondary">
            Cafe
          </Button>
        </Link>
        <Link to="/workspace/agro">
          <Button size="sm" variant="secondary">
            Agriculture
          </Button>
        </Link>
        <Link to="/workspace/legal">
          <Button size="sm" variant="secondary">
            Legal
          </Button>
        </Link>
        <Link to="/workspace/crypto">
          <Button size="sm" variant="secondary">
            Bidex
          </Button>
        </Link>
        <Link to="/workspace/drone">
          <Button size="sm" variant="secondary">
            Drone
          </Button>
        </Link>
        <Link to="/platform-builder/mission-control">
          <Button size="sm" variant="secondary">
            Mission Control
          </Button>
        </Link>
        <Link to="/pilot/production">
          <Button size="sm" variant="secondary">
            Production Readiness
          </Button>
        </Link>
      </div>

      {error ? (
        <div className="mt-4">
          <EmptyState
            title="Telemetry warning"
            description={error}
            actionLabel="Open Drone"
            actionTo="/workspace/drone"
          />
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card title="Operational metrics">
          <ul className="eds-type-small space-y-1">
            <li>User sessions: {pilotSnap?.sessions ?? "—"}</li>
            <li>
              Workflow completion:{" "}
              {pilotSnap?.workflowCompletionRate != null ? `${pilotSnap.workflowCompletionRate}%` : "—"}
            </li>
            <li>Avg processing: {pilotSnap?.avgProcessingMs != null ? `${pilotSnap.avgProcessingMs} ms` : "—"}</li>
            <li>API timing samples: {pilotSnap?.apiResponseSamples ?? 0}</li>
            <li>AI timing samples: {pilotSnap?.aiResponseSamples ?? 0}</li>
            <li>Business events: {pilotSnap?.businessEvents ?? 0}</li>
            <li>
              System health:{" "}
              <Badge tone={pilotSnap?.systemHealthy ? "success" : "warning"}>
                {pilotSnap?.systemHealthy ? "healthy" : "check"}
              </Badge>
            </li>
            <li>MC probe: {mcStatus ? "ok" : "—"}</li>
            <li>
              OBS:{" "}
              {obsHealth?.status === "ok" || obsHealth?.enterprise_observability_ready ? "ready" : "—"}
            </li>
            <li>
              EPD:{" "}
              {epdHealth?.status === "ok" || epdHealth?.production_platform_ready ? "ready" : "—"}
            </li>
            <li>EPR: {eprHealth?.status === "ok" ? "ready" : eprHealth ? "partial" : "—"}</li>
          </ul>
        </Card>

        <Card title="Performance chart">
          <Charts
            labels={["Sessions", "Completion%", "Avg ms", "Metrics", "Logs", "Probes"]}
            values={chartValues}
          />
        </Card>

        <Card title="Errors per module">
          {pilotSnap && Object.keys(pilotSnap.errorsPerModule).length ? (
            <ul className="eds-type-small space-y-1">
              {Object.entries(pilotSnap.errorsPerModule).map(([mod, n]) => (
                <li key={mod}>
                  {mod}: <Badge tone="warning">{n}</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">No module errors recorded this session.</p>
          )}
        </Card>

        <Card title="Business OBS dashboard">
          <p className="eds-type-small text-[var(--eds-text-muted)]">
            id: {String(pilotSnap?.businessDash?.dashboard_id ?? "—")}
          </p>
          <pre className="mt-2 max-h-40 overflow-auto eds-type-small">
            {JSON.stringify(pilotSnap?.businessDash?.metrics ?? {}, null, 2)}
          </pre>
        </Card>

        <Card title="Platform OBS dashboard">
          <p className="eds-type-small text-[var(--eds-text-muted)]">
            id: {String(pilotSnap?.platformDash?.dashboard_id ?? "—")}
          </p>
          <pre className="mt-2 max-h-40 overflow-auto eds-type-small">
            {JSON.stringify(pilotSnap?.platformDash?.metrics ?? {}, null, 2)}
          </pre>
        </Card>

        <Card title="Notifications">
          <NotificationsPanel />
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="Role journeys (login → completion)">
          <Table headers={["Role", "Match", "Steps", "Status"]}>
            {journeys.map((j) => (
              <tr key={j.role} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{j.title}</td>
                <td className="px-3 py-2">
                  <Badge tone={j.roleMatch ? "success" : "default"}>{j.roleMatch ? "current" : "—"}</Badge>
                </td>
                <td className="px-3 py-2 eds-type-small">
                  {j.steps.map((s) => (
                    <div key={s.id}>
                      <Link className="underline" to={s.route}>
                        {s.label}
                      </Link>
                    </div>
                  ))}
                </td>
                <td className="px-3 py-2">
                  <Badge tone={j.ok ? "success" : "warning"}>{j.ok ? "reachable" : "auth required"}</Badge>
                </td>
              </tr>
            ))}
          </Table>
        </Card>

        <Card title="Central Pilot Feedback">
          <p className="mb-2 eds-type-small text-[var(--eds-text-muted)]">
            Routes to EPR → EOC → EPI. ELE classifies; Critical/High open OBS incidents. Every item has a
            trace id.
          </p>
          <div className="grid gap-2">
            <Select value={fbCategory} onChange={(e) => setFbCategory(e.target.value as FeedbackCategory)}>
              <option value="user_feedback">User feedback</option>
              <option value="ai_feedback">AI feedback</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="suggestion">Suggestion</option>
              <option value="ux_issue">UX issue</option>
              <option value="missing_feature">Missing feature</option>
            </Select>
            <Input
              value={fbFeature}
              onChange={(e) => setFbFeature(e.target.value)}
              aria-label="Feature / module"
              placeholder="feature / module"
            />
            <Input
              value={fbMessage}
              onChange={(e) => setFbMessage(e.target.value)}
              aria-label="Feedback message"
              placeholder="Describe the issue or idea"
            />
            <Button size="sm" disabled={fbBusy || !fbMessage.trim()} onClick={() => void onSubmitFeedback()}>
              Submit feedback
            </Button>
          </div>
          {feedbackItems.length ? (
            <Table headers={["Severity", "Module", "Trace", "Category"]}>
              {feedbackItems.slice(0, 8).map((f) => (
                <tr key={f.trace_id} className="border-t border-[var(--ew-border)]">
                  <td className="px-3 py-2">
                    <Badge
                      tone={
                        f.severity === "Critical" || f.severity === "High"
                          ? "danger"
                          : f.severity === "Medium"
                            ? "warning"
                            : "default"
                      }
                    >
                      {f.severity}
                    </Badge>
                  </td>
                  <td className="px-3 py-2">{f.module}</td>
                  <td className="px-3 py-2 eds-type-small">{f.trace_id}</td>
                  <td className="px-3 py-2">{f.category}</td>
                </tr>
              ))}
            </Table>
          ) : (
            <p className="mt-3 eds-type-small text-[var(--eds-text-muted)]">No feedback submitted yet.</p>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Web completion audit (7 workspaces)">
          <p className="mb-2 eds-type-small text-[var(--eds-text-muted)]">
            {webSummary.ecosystems} ecosystems · checklist ready {webSummary.readyCount}/
            {webSummary.productionItems} · score {readinessScore}%
          </p>
          <Table headers={["Workspace", "Route", "UX contract"]}>
            {WORKSPACE_HEALTH_PROBES.map((w) => (
              <tr key={w.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{w.label}</td>
                <td className="px-3 py-2">
                  <Link className="underline" to={w.route}>
                    {w.route}
                  </Link>
                </td>
                <td className="px-3 py-2 eds-type-small">{w.expects.join(" · ")}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Connected modules">
          <ul className="eds-type-small columns-2 gap-4 space-y-1">
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
