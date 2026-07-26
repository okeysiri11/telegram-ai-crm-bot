/**
 * First live Automotive business workflow — Sprint 30.6.
 * Customer → Auth → Dashboard → CRM → Lead → AI Concierge → Task → Notification → MC → Analytics
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
import {
  runAutomotiveLiveWorkflow,
  type WorkflowStepResult,
} from "./automotiveWorkflow";
import { isJwtToken } from "@/auth/identityApi";

export function AutomotiveLiveWorkflowPage() {
  const authUser = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const authMode = useAuthStore((s) => s.authMode);
  const validateSession = useAuthStore((s) => s.validateSession);
  const org = useWorkspaceStore((s) => s.workspace.company);
  const core = useWebCore();

  const [firstName, setFirstName] = useState("Pilot");
  const [lastName, setLastName] = useState("Customer");
  const [customerEmail, setCustomerEmail] = useState(
    `pilot.customer+${Date.now().toString(36)}@demo.corp`,
  );
  const [customerPassword, setCustomerPassword] = useState("pilot-demo");
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
      await telemetry.businessEvent("automotive_workflow_start");
      await telemetry.aiActivity("concierge", "automotive_pilot_workflow_begin");
      const result = await runAutomotiveLiveWorkflow({
        customerEmail,
        customerPassword,
        firstName,
        lastName,
        organizationId: org || "org_demo",
      });
      setSteps(result.steps);
      setTotalMs(result.totalMs);
      setSuccess(result.success);
      pilotMetrics.recordWorkflow(result.success, result.totalMs);
      for (const s of result.steps) {
        pilotMetrics.recordApiTiming(s.id, s.durationMs, s.ok);
        if (s.id === "ai_concierge") pilotMetrics.recordAiTiming(s.durationMs);
        if (!s.ok) pilotMetrics.recordModuleError(s.id.startsWith("crm") ? "automotive" : s.id);
      }
      await telemetry.businessEvent(
        result.success ? "automotive_workflow_success" : "automotive_workflow_partial",
        result.totalMs,
      );
      await telemetry.apiCall("automotive/live-workflow", result.totalMs, result.success);
      if (!result.success) {
        const failed = result.steps.filter((s) => !s.ok);
        setError(failed.map((f) => `${f.label}: ${f.error}`).join(" · "));
        await telemetry.error("automotive_workflow_step_failed");
      } else {
        await telemetry.audit("automotive_workflow_complete", `ms=${result.totalMs}`);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setSuccess(false);
      await telemetry.error("automotive_workflow", e instanceof Error ? e : undefined);
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Live Workflow</Badge>
        <Badge>Sprint 30.7</Badge>
        <Badge>Automotive</Badge>
        <Badge>{authMode || "—"}</Badge>
        {isJwtToken(accessToken) ? <Badge tone="success">JWT</Badge> : <Badge tone="warning">ISAM token</Badge>}
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">First Live Automotive Workflow</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        End-to-end business flow on existing APIs: Customer → Authentication → Dashboard → CRM → Lead →
        AI Concierge → Task → Notification → Mission Control → Analytics. No parallel stacks.
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
        <Card title="Customer (portal auth)">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} aria-label="First name" />
            <Input value={lastName} onChange={(e) => setLastName(e.target.value)} aria-label="Last name" />
            <Input
              className="sm:col-span-2"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              aria-label="Customer email"
            />
            <Input
              className="sm:col-span-2"
              type="password"
              value={customerPassword}
              onChange={(e) => setCustomerPassword(e.target.value)}
              aria-label="Customer password"
            />
          </div>
        </Card>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={busy} onClick={() => void run()}>
          {busy ? "Running…" : "Execute live workflow"}
        </Button>
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
        <Link to="/portals/customer">
          <Button size="sm" variant="secondary">
            Customer Portal
          </Button>
        </Link>
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
            description="Fill customer fields and run the workflow. Staff must be logged in via production authentication (ISAM + optional platform JWT)."
          />
        </div>
      )}
    </WorkspaceLayout>
  );
}
