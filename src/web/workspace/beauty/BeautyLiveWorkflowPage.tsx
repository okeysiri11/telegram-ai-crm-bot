/**
 * Beauty live workflow — Sprint 30.8.
 * Client → Auth → Appointment → Calendar → AI Reminder → CRM → Owner Dashboard → MC → Analytics
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input, Table } from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useWebCore } from "@/shell/WebCoreProvider";
import { telemetry } from "@/integrations/telemetry";
import { pilotMetrics } from "@/integrations/pilotMetrics";
import { runBeautyLiveWorkflow, type WorkflowStepResult } from "./beautyWorkflow";
import { isJwtToken } from "@/auth/identityApi";
import { ECOSYSTEM_REUSE_MATRIX } from "../ecosystem-template";

export function BeautyLiveWorkflowPage() {
  const authUser = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const authMode = useAuthStore((s) => s.authMode);
  const validateSession = useAuthStore((s) => s.validateSession);
  const org = useWorkspaceStore((s) => s.workspace.company);
  const core = useWebCore();

  const [clientName, setClientName] = useState("Pilot Client");
  const [clientEmail, setClientEmail] = useState(
    `pilot.beauty+${Date.now().toString(36)}@demo.corp`,
  );
  const [busy, setBusy] = useState(false);
  const [steps, setSteps] = useState<WorkflowStepResult[]>([]);
  const [totalMs, setTotalMs] = useState<number | null>(null);
  const [success, setSuccess] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    setSteps([]);
    setSuccess(null);
    setTotalMs(null);
    try {
      const sessionOk = await validateSession();
      if (!sessionOk || !authUser) {
        throw new Error("Staff session invalid — login with production authentication first.");
      }
      await telemetry.businessEvent("beauty_workflow_start");
      await telemetry.aiActivity("concierge", "beauty_pilot_workflow_begin");
      const result = await runBeautyLiveWorkflow({
        clientName,
        clientEmail,
        organizationId: org || "org_demo",
      });
      setSteps(result.steps);
      setTotalMs(result.totalMs);
      setSuccess(result.success);
      pilotMetrics.recordWorkflow(result.success, result.totalMs);
      for (const s of result.steps) {
        pilotMetrics.recordApiTiming(s.id, s.durationMs, s.ok);
        if (s.id === "ai_concierge") pilotMetrics.recordAiTiming(s.durationMs);
        if (!s.ok) pilotMetrics.recordModuleError(s.id.includes("bos") || s.id.includes("crm") ? "beauty" : s.id);
      }
      await telemetry.businessEvent(
        result.success ? "beauty_workflow_success" : "beauty_workflow_partial",
        result.totalMs,
      );
      await telemetry.apiCall("beauty/live-workflow", result.totalMs, result.success);
      if (!result.success) {
        const failed = result.steps.filter((s) => !s.ok);
        setError(failed.map((f) => `${f.label}: ${f.error}`).join(" · "));
        await telemetry.error("beauty_workflow_step_failed");
      } else {
        await telemetry.audit("beauty_workflow_complete", `ms=${result.totalMs}`);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setSuccess(false);
      await telemetry.error("beauty_workflow", e instanceof Error ? e : undefined);
    } finally {
      setBusy(false);
    }
  }

  const reuseKeys = Object.keys(ECOSYSTEM_REUSE_MATRIX) as (keyof typeof ECOSYSTEM_REUSE_MATRIX)[];

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Live Workflow</Badge>
        <Badge>Sprint 30.8</Badge>
        <Badge>Beauty Pilot</Badge>
        <Badge>{authMode || "—"}</Badge>
        {isJwtToken(accessToken) ? <Badge tone="success">JWT</Badge> : <Badge tone="warning">ISAM token</Badge>}
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">Beauty Business Ecosystem Workflow</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Second internal pilot on the shared Enterprise Platform: Client → Authentication → Appointment →
        Calendar → AI Reminder → CRM → Owner Dashboard → Mission Control → Analytics. Reuses Automotive
        template patterns — no duplicated services.
      </p>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Staff session">
          <ul className="eds-type-small space-y-1">
            <li>User: {authUser?.email || "—"}</li>
            <li>Role: {authUser?.roleId || "—"}</li>
            <li>Org: {core.organization}</li>
            <li>Permissions: {(authUser?.permissions || core.permissions).join(", ") || "—"}</li>
            <li>Auth mode: {authMode || "—"}</li>
          </ul>
        </Card>
        <Card title="Client">
          <div className="grid gap-2">
            <Input value={clientName} onChange={(e) => setClientName(e.target.value)} aria-label="Client name" />
            <Input
              value={clientEmail}
              onChange={(e) => setClientEmail(e.target.value)}
              aria-label="Client email"
            />
          </div>
        </Card>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={busy} onClick={() => void run()}>
          {busy ? "Running…" : "Execute Beauty workflow"}
        </Button>
        <Link to="/workspace/auto">
          <Button size="sm" variant="secondary">
            Automotive reference
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

      <div className="mt-4">
        <Card title="Platform reuse (shared with Automotive)">
          <ul className="eds-type-small grid gap-1 sm:grid-cols-2">
            {reuseKeys.map((k) => (
              <li key={k}>
                {k}: {ECOSYSTEM_REUSE_MATRIX[k].source}
              </li>
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
            title="Ready to execute"
            description="Enter client details and run. Staff must be logged in via production authentication. Beauty uses BOS/BWS/BCJ + shared Concierge/Comms/MC/OBS."
          />
        </div>
      )}
    </WorkspaceLayout>
  );
}
