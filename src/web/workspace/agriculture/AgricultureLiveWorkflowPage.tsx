/**
 * Agriculture live pilot UI — Sprint 31.1.
 * Fourth operational Business Ecosystem on the shared Enterprise Platform.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input, Table } from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useWebCore } from "@/shell/WebCoreProvider";
import { telemetry } from "@/integrations/telemetry";
import { pilotMetrics } from "@/integrations/pilotMetrics";
import { runAgricultureLiveWorkflow, type WorkflowStepResult } from "./agricultureWorkflow";
import { isJwtToken } from "@/auth/identityApi";
import { computeReusePercentage, CROSS_ECOSYSTEM_PATTERNS } from "../ecosystem-template";

export function AgricultureLiveWorkflowPage() {
  const authUser = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const authMode = useAuthStore((s) => s.authMode);
  const validateSession = useAuthStore((s) => s.validateSession);
  const org = useWorkspaceStore((s) => s.workspace.company);
  const core = useWebCore();

  const [farmerName, setFarmerName] = useState("Pilot Farmer");
  const [farmerEmail, setFarmerEmail] = useState(
    `pilot.agro+${Date.now().toString(36)}@demo.corp`,
  );
  const [busy, setBusy] = useState(false);
  const [steps, setSteps] = useState<WorkflowStepResult[]>([]);
  const [totalMs, setTotalMs] = useState<number | null>(null);
  const [success, setSuccess] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reusePercent, setReusePercent] = useState<number | null>(null);

  const reuseAudit = useMemo(() => computeReusePercentage(), []);

  async function run() {
    setBusy(true);
    setError(null);
    setSteps([]);
    setSuccess(null);
    setTotalMs(null);
    setReusePercent(null);
    try {
      const sessionOk = await validateSession();
      if (!sessionOk || !authUser) {
        throw new Error("Staff session invalid — login with production authentication first.");
      }
      await telemetry.businessEvent("agriculture_workflow_start");
      await telemetry.aiActivity("concierge", "agriculture_pilot_execution_begin");
      pilotMetrics.recordSession();
      const result = await runAgricultureLiveWorkflow({
        farmerName,
        farmerEmail,
        organizationId: org || "org_demo",
      });
      setSteps(result.steps);
      setTotalMs(result.totalMs);
      setSuccess(result.success);
      setReusePercent(result.reusePercent ?? reuseAudit.reusePercent);
      pilotMetrics.recordWorkflow(result.success, result.totalMs);
      pilotMetrics.recordBusinessEvent("agriculture_trade");
      for (const s of result.steps) {
        pilotMetrics.recordApiTiming(s.id, s.durationMs, s.ok);
        if (s.id === "ai_concierge" || s.id === "ai_team" || s.id === "ai_marketing" || s.id === "ai_agronomist") {
          pilotMetrics.recordAiTiming(s.durationMs);
        }
        if (!s.ok) pilotMetrics.recordModuleError("agriculture");
      }
      await telemetry.businessEvent(
        result.success ? "agriculture_workflow_success" : "agriculture_workflow_partial",
        result.totalMs,
      );
      await telemetry.apiCall("agriculture/live-workflow", result.totalMs, result.success);
      if (!result.success) {
        const failed = result.steps.filter((s) => !s.ok);
        setError(failed.map((f) => `${f.label}: ${f.error}`).join(" · "));
        await telemetry.error("agriculture_workflow_step_failed");
      } else {
        await telemetry.audit("agriculture_workflow_complete", `ms=${result.totalMs}`);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setSuccess(false);
      await telemetry.error("agriculture_workflow", e instanceof Error ? e : undefined);
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Operational Pilot</Badge>
        <Badge>Sprint 31.1</Badge>
        <Badge>Agriculture</Badge>
        <Badge tone="success">Reuse {reuseAudit.reusePercent}%</Badge>
        <Badge>Cross {reuseAudit.crossEcosystemPercent}%</Badge>
        <Badge>{authMode || "—"}</Badge>
        {isJwtToken(accessToken) ? <Badge tone="success">JWT</Badge> : <Badge tone="warning">ISAM token</Badge>}
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">Agriculture Pilot Execution</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Fourth operational Business Ecosystem: Farmer → CRM → Harvest → Warehouse → Commodity Sale →
        Contract → Shipment (sea freight / containers / customs) → Mission Control → Analytics. Reuses
        existing Agro Marketplace + Supply Chain APIs. Auto / Beauty / Cafe unchanged.
      </p>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Staff session">
          <ul className="eds-type-small space-y-1">
            <li>User: {authUser?.email || "—"}</li>
            <li>Role: {authUser?.roleId || "—"}</li>
            <li>Org: {core.organization}</li>
            <li>Permissions: {(authUser?.permissions || core.permissions).join(", ") || "—"}</li>
          </ul>
        </Card>
        <Card title="Farmer">
          <div className="grid gap-2">
            <Input value={farmerName} onChange={(e) => setFarmerName(e.target.value)} aria-label="Farmer name" />
            <Input
              value={farmerEmail}
              onChange={(e) => setFarmerEmail(e.target.value)}
              aria-label="Farmer email"
            />
          </div>
        </Card>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={busy} onClick={() => void run()}>
          {busy ? "Running…" : "Execute Agriculture pilot"}
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
        <Link to="/platform-builder/mission-control">
          <Button size="sm" variant="secondary">
            Mission Control
          </Button>
        </Link>
        <Link to="/pilot">
          <Button size="sm" variant="secondary">
            Pilot Dashboard
          </Button>
        </Link>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card
          title={`Enterprise reuse — ${reuseAudit.reusePercent}% (${reuseAudit.sharedCount}/${reuseAudit.totalCount})`}
        >
          <Table headers={["Dimension", "Auto", "Beauty", "Cafe", "Agro"]}>
            {reuseAudit.dimensions.map((d) => (
              <tr key={d.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2 eds-type-small">{d.id}</td>
                <td className="px-3 py-2">{d.automotive ? "✓" : "—"}</td>
                <td className="px-3 py-2">{d.beauty ? "✓" : "—"}</td>
                <td className="px-3 py-2">{d.cafe ? "✓" : "—"}</td>
                <td className="px-3 py-2">{d.agriculture ? "✓" : "—"}</td>
              </tr>
            ))}
          </Table>
        </Card>
        <Card title="Reusable patterns (4 ecosystems)">
          <ul className="eds-type-small space-y-1">
            {CROSS_ECOSYSTEM_PATTERNS.map((p) => (
              <li key={p}>• {p}</li>
            ))}
          </ul>
        </Card>
      </div>

      {error ? (
        <div className="mt-4">
          <EmptyState title="Workflow warnings / errors" description={error} />
        </div>
      ) : null}

      {totalMs !== null ? (
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge tone={success ? "success" : "warning"}>
            {success ? "All steps succeeded" : "Completed with failures"}
          </Badge>
          <Badge>Total {totalMs} ms</Badge>
          <Badge>
            {steps.filter((s) => s.ok).length}/{steps.length} steps
          </Badge>
          {reusePercent != null ? <Badge tone="success">Reuse {reusePercent}%</Badge> : null}
        </div>
      ) : null}

      {steps.length ? (
        <div className="mt-6">
          <Card title="Execution log">
            <Table headers={["Step", "Status", "ms", "Detail"]}>
              {steps.map((s) => (
                <tr key={s.id} className="border-t border-[var(--ew-border)]">
                  <td className="px-3 py-2">{s.label}</td>
                  <td className="px-3 py-2">
                    <Badge tone={s.ok ? "success" : "danger"}>{s.ok ? "ok" : "error"}</Badge>
                  </td>
                  <td className="px-3 py-2">{s.durationMs}</td>
                  <td className="px-3 py-2 eds-type-small text-[var(--eds-text-muted)]">
                    {s.error || s.detail || "—"}
                  </td>
                </tr>
              ))}
            </Table>
          </Card>
        </div>
      ) : (
        <div className="mt-6">
          <EmptyState
            title="Ready to execute Agriculture pilot"
            description="Validates farm CRM, harvest, warehouse, grain marketplace sale, export contracts, sea freight, containers, customs, AI Team, and Mission Control on existing agro APIs."
          />
        </div>
      )}
    </WorkspaceLayout>
  );
}
