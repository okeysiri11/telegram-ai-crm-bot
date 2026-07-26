/**
 * External Pilot Onboarding Wizard — Sprint 32.1.
 * Reuses tenancy + EON + EPR APIs — no new onboarding engine.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input, Select, Table } from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { hubIntegrations } from "@/integrations/hub";
import { apiFetch } from "@/integrations/apiClient";
import { telemetry } from "@/integrations/telemetry";
import { PLATFORM_BUILDER_VERSION } from "../../platform-builder/types";
import { ONBOARDING_ECOSYSTEMS } from "../pilot/webCompletionAudit";

type Dict = Record<string, unknown>;

const INDUSTRIES = [
  { value: "automotive", label: "Automotive" },
  { value: "beauty", label: "Beauty" },
  { value: "cafe", label: "Cafe / F&B" },
  { value: "agriculture", label: "Agriculture" },
  { value: "legal", label: "Legal" },
  { value: "crypto", label: "Bidex / Crypto" },
  { value: "drone", label: "Drone" },
];

export function ExternalPilotOnboardPage() {
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("beauty");
  const [licenseTier, setLicenseTier] = useState("business");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [tenant, setTenant] = useState<Dict | null>(null);
  const [wizard, setWizard] = useState<Dict | null>(null);
  const [goLive, setGoLive] = useState<Dict | null>(null);
  const [firstLaunch, setFirstLaunch] = useState<Dict | null>(null);

  function push(msg: string) {
    setLog((prev) => [...prev, msg]);
  }

  async function runOnboarding() {
    if (!companyName.trim()) {
      setError("Company name is required");
      return;
    }
    setBusy(true);
    setError(null);
    setLog([]);
    setTenant(null);
    setWizard(null);
    setGoLive(null);
    setFirstLaunch(null);
    const started = performance.now();
    try {
      // 1. Tenancy bootstrap onboarding
      const tnRes = await apiFetch(`${hubIntegrations.tenancy}/onboarding`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: companyName.trim(),
          license_tier: licenseTier,
          language: "en",
          currency: "USD",
        }),
      });
      const tnBody = (await tnRes.json()) as Dict;
      if (!tnRes.ok) throw new Error(String(tnBody.error || `Tenancy HTTP ${tnRes.status}`));
      setTenant(tnBody);
      push(`Tenant provisioned: ${String(tnBody.tenant_id ?? tnBody.name ?? "ok")}`);

      // 2. EON wizard start
      const wizRes = await apiFetch(`${hubIntegrations.onboarding}/wizard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_name: companyName.trim(), industry }),
      });
      let wiz = (await wizRes.json()) as Dict;
      if (!wizRes.ok) throw new Error(String(wiz.error || `Wizard HTTP ${wizRes.status}`));
      push(`Wizard started: ${String(wiz.wizard_id)} · step ${String(wiz.current_step)}`);

      // 3. Advance through remaining wizard steps
      const steps = Array.isArray(wiz.steps) ? (wiz.steps as string[]) : [];
      let guard = 0;
      while (guard < 12 && String(wiz.current_step || "") && !(wiz.completed === true)) {
        const completed = Array.isArray(wiz.completed_steps) ? (wiz.completed_steps as string[]) : [];
        if (steps.length && completed.length >= steps.length) break;
        const advRes = await apiFetch(`${hubIntegrations.onboarding}/wizard`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            wizard_id: wiz.wizard_id,
            step_data: { company_name: companyName.trim(), industry, confirmed: true },
          }),
        });
        wiz = (await advRes.json()) as Dict;
        if (!advRes.ok) throw new Error(String(wiz.error || `Advance HTTP ${advRes.status}`));
        push(`Advanced → ${String(wiz.current_step)}`);
        guard += 1;
        if (wiz.status === "complete" || wiz.completed === true) break;
      }
      setWizard(wiz);

      // 4. Initial config
      const cfgRes = await apiFetch(`${hubIntegrations.onboarding}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wizard_id: wiz.wizard_id }),
      });
      const cfg = (await cfgRes.json()) as Dict;
      if (!cfgRes.ok) throw new Error(String(cfg.error || `Config HTTP ${cfgRes.status}`));
      push("Initial configuration applied");

      // 5. Readiness
      const readyRes = await apiFetch(
        `${hubIntegrations.onboarding}/readiness?wizard_id=${encodeURIComponent(String(wiz.wizard_id))}`,
      );
      const ready = (await readyRes.json()) as Dict;
      if (!readyRes.ok) throw new Error(String(ready.error || `Readiness HTTP ${readyRes.status}`));
      push(`Readiness: ${String(ready.status ?? ready.score ?? "ok")}`);

      // 6. Go live
      const liveRes = await apiFetch(`${hubIntegrations.onboarding}/go-live`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wizard_id: wiz.wizard_id, completed: true }),
      });
      const live = (await liveRes.json()) as Dict;
      if (!liveRes.ok) throw new Error(String(live.error || `Go-live HTTP ${liveRes.status}`));
      setGoLive(live);
      push("Organization go-live completed");

      // 7. EPR first-launch
      const flRes = await apiFetch(`${hubIntegrations.pilotReadiness}/first-launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          organization: companyName.trim(),
          industry,
          tenant_id: tnBody.tenant_id,
        }),
      });
      const fl = (await flRes.json()) as Dict;
      if (flRes.ok) {
        setFirstLaunch(fl);
        push("EPR first-launch recorded");
      } else {
        push(`EPR first-launch skipped: ${String(fl.error || flRes.status)}`);
      }

      await telemetry.audit("external_pilot_onboard", String(tnBody.tenant_id || companyName));
      await telemetry.apiCall("pilot/onboard", performance.now() - started, true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Onboarding failed");
      await telemetry.apiCall("pilot/onboard", performance.now() - started, false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">External Pilot Onboarding</Badge>
        <Badge>Sprint 32.1</Badge>
        <Badge>PB {PLATFORM_BUILDER_VERSION}</Badge>
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">Organization Onboarding</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Guided setup for external pilot organizations. Reuses Tenancy, Enterprise Onboarding (EON), and EPR —
        no duplicated services.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/pilot">
          <Button size="sm" variant="secondary">
            Pilot Dashboard
          </Button>
        </Link>
        <Link to="/pilot/invite">
          <Button size="sm" variant="secondary">
            Invite Users
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
          <EmptyState title="Onboarding warning" description={error} actionLabel="Open Pilot" actionTo="/pilot" />
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="1. Organization registration">
          <div className="grid gap-2">
            <Input
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Company name"
              aria-label="Company name"
            />
            <Select value={industry} onChange={(e) => setIndustry(e.target.value)} aria-label="Industry">
              {INDUSTRIES.map((i) => (
                <option key={i.value} value={i.value}>
                  {i.label}
                </option>
              ))}
            </Select>
            <Select
              value={licenseTier}
              onChange={(e) => setLicenseTier(e.target.value)}
              aria-label="License tier"
            >
              <option value="starter">Starter</option>
              <option value="business">Business</option>
              <option value="enterprise">Enterprise</option>
            </Select>
            <Button size="sm" disabled={busy || !companyName.trim()} onClick={() => void runOnboarding()}>
              {busy ? "Running wizard…" : "Run full onboarding"}
            </Button>
          </div>
          <p className="mt-3 eds-type-small text-[var(--eds-text-muted)]">
            Executes: tenant activation → wizard steps → config → readiness → go-live → first-launch.
          </p>
        </Card>

        <Card title="Progress log">
          {log.length ? (
            <ul className="eds-type-small space-y-1">
              {log.map((line, i) => (
                <li key={`${i}-${line}`}>
                  <Badge tone="success">{i + 1}</Badge> {line}
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">Awaiting onboarding run.</p>
          )}
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card title="Tenant">
          <pre className="max-h-40 overflow-auto eds-type-small">{JSON.stringify(tenant ?? {}, null, 2)}</pre>
        </Card>
        <Card title="Wizard">
          <pre className="max-h-40 overflow-auto eds-type-small">{JSON.stringify(wizard ?? {}, null, 2)}</pre>
        </Card>
        <Card title="Go-live / first-launch">
          <pre className="max-h-40 overflow-auto eds-type-small">
            {JSON.stringify({ goLive, firstLaunch }, null, 2)}
          </pre>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="2. Business ecosystem selection">
          <Table headers={["Ecosystem", "Workspace"]}>
            {ONBOARDING_ECOSYSTEMS.map((e) => (
              <tr key={e.id} className="border-t border-[var(--ew-border)]">
                <td className="px-3 py-2">{e.label}</td>
                <td className="px-3 py-2">
                  <Link className="underline" to={e.route}>
                    {e.route}
                  </Link>
                </td>
              </tr>
            ))}
          </Table>
        </Card>
        <Card title="3. Next activation steps">
          <ul className="eds-type-small space-y-2">
            <li>
              Owner / user invitations →{" "}
              <Link className="underline" to="/pilot/invite">
                /pilot/invite
              </Link>
            </li>
            <li>
              Role assignment →{" "}
              <Link className="underline" to="/identity/roles">
                /identity/roles
              </Link>
            </li>
            <li>
              AI Team activation →{" "}
              <Link className="underline" to="/platform-builder/ai-team">
                /platform-builder/ai-team
              </Link>
            </li>
            <li>
              Empty workspace guidance →{" "}
              <Link className="underline" to="/workspace">
                /workspace
              </Link>
            </li>
          </ul>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
