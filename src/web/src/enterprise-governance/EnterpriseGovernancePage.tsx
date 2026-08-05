/**
 * Enterprise Governance UI — Sprint 33.9.
 * Composition over Autonomy / RBAC / Runtime — no new Engines.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useAuthStore } from "@/auth/authStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveGovernance, type ExecApprovalRow } from "./deriveGovernance";

const QUEUE_FILTERS: Array<ExecApprovalRow["queue"] | "all"> = [
  "all",
  "pending",
  "approved",
  "rejected",
  "expired",
  "critical",
];

const QUEUE_TONE: Record<ExecApprovalRow["queue"], "default" | "success" | "danger" | "warning"> = {
  pending: "warning",
  approved: "success",
  rejected: "danger",
  expired: "default",
  critical: "danger",
};

export function EnterpriseGovernancePage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const ws = useWorkspaceStore((s) => s.workspace);
  const user = useAuthStore((s) => s.user);
  const company = first.companyName || ws.company || "Enterprise";
  const [queue, setQueue] = useState<(typeof QUEUE_FILTERS)[number]>("all");

  const gov = useMemo(
    () =>
      deriveGovernance(snapshot, {
        notifications,
        roleId: user?.roleId || first.roleId,
        permissions: user?.permissions || ["read", "write"],
      }),
    [snapshot, notifications, user?.roleId, user?.permissions, first.roleId],
  );

  const approvals =
    queue === "all" ? gov.approvalQueue : gov.approvalQueue.filter((a) => a.queue === queue);

  return (
    <WorkspaceLayout>
      <div className="gov-page" data-testid="enterprise-governance">
        <header className="gov-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">
              Enterprise Governance · Sprint 33.9
            </p>
            <h1 className="gov-title">Governance · {company}</h1>
            <p className="eds-type-body">
              Политики, комплаенс, аудит, риски и контроль AI — композиция поверх Autonomy Approval, RBAC и
              Runtime.
            </p>
          </div>
          <div className="gov-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Badge tone="success">Compliance {gov.compliance.compliancePct}%</Badge>
            <Link to="/platform-builder/autonomy" className="eds-type-small text-[var(--eds-primary)]">
              Approval Center →
            </Link>
            <Link to="/platform-builder/control-tower" className="eds-type-small text-[var(--eds-primary)]">
              Control Tower →
            </Link>
          </div>
        </header>

        {/* SECTION 7 — Compliance Center */}
        <Card aria-label="Compliance Center">
          <div className="gov-section-head">
            <h2>Compliance Center</h2>
          </div>
          <div className="gov-scores">
            <div className="gov-score">
              <span className="eds-type-small text-[var(--eds-muted)]">Audit Score</span>
              <strong>{gov.compliance.auditScore}</strong>
            </div>
            <div className="gov-score">
              <span className="eds-type-small text-[var(--eds-muted)]">Security Score</span>
              <strong>{gov.compliance.securityScore}</strong>
            </div>
            <div className="gov-score">
              <span className="eds-type-small text-[var(--eds-muted)]">Compliance %</span>
              <strong>{gov.compliance.compliancePct}%</strong>
            </div>
            <div className="gov-score">
              <span className="eds-type-small text-[var(--eds-muted)]">Policy Health</span>
              <strong>{gov.compliance.policyHealth}</strong>
            </div>
          </div>
        </Card>

        {/* SECTION 1 — Enterprise Policies */}
        <Card aria-label="Enterprise Policies">
          <div className="gov-section-head">
            <h2>Enterprise Policies</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Financial · Security · Legal · Privacy · HR · Ops · AI · Automation
            </span>
          </div>
          <div className="gov-policies">
            {gov.policies.map((p) => (
              <div key={p.id} className={`gov-pol is-${p.status}`}>
                <div className="flex flex-wrap justify-between gap-1">
                  <strong>{p.label}</strong>
                  <Badge
                    tone={p.status === "breach" ? "danger" : p.status === "watch" ? "warning" : "success"}
                  >
                    {p.status}
                  </Badge>
                </div>
                <p className="eds-type-small text-[var(--eds-muted)]">{p.summary}</p>
                <span className="eds-type-small">
                  {p.severity} · {p.permissionHint}
                </span>
                <span className="eds-type-small">{p.detail}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 2 — Policy Validation */}
        <Card aria-label="Policy Validation">
          <div className="gov-section-head">
            <h2>Policy Validation</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Policy → Permission → Approval → Execution
            </span>
          </div>
          <div className="gov-pipeline">
            {gov.validations.map((v) => (
              <div key={v.actionId} className="gov-val">
                <div className="flex flex-wrap justify-between gap-2">
                  <strong className="eds-type-small">{v.actionTitle}</strong>
                  <Badge tone={v.allowed ? "success" : "warning"}>
                    {v.allowed ? "allowed" : v.blockedBy || "waiting"}
                  </Badge>
                </div>
                <div className="gov-steps">
                  {v.steps.map((s) => (
                    <div key={s.id} className={`gov-step is-${s.status}`}>
                      <strong>{s.label}</strong>
                      <Badge>{s.status}</Badge>
                      <p className="eds-type-small text-[var(--eds-muted)]">{s.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {!gov.validations.length ? (
              <p className="eds-type-small text-[var(--eds-muted)]">Нет активных действий для проверки</p>
            ) : null}
          </div>
        </Card>

        {/* SECTION 3 — Executive Approval Center */}
        <Card aria-label="Executive Approval Center">
          <div className="gov-section-head">
            <h2>Executive Approval Center</h2>
            <Link to="/platform-builder/autonomy" className="eds-type-small text-[var(--eds-primary)]">
              Autonomy HITL →
            </Link>
          </div>
          <div className="gov-queue-tabs">
            {QUEUE_FILTERS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => {
                  setQueue(q);
                  void telemetry.userActivity(`gov_queue:${q}`);
                }}
              >
                <Badge tone={queue === q ? "success" : "default"}>
                  {q === "all"
                    ? `All (${gov.approvalQueue.length})`
                    : `${q} (${gov.approvalQueue.filter((a) => a.queue === q).length})`}
                </Badge>
              </button>
            ))}
          </div>
          <ul className="gov-queue-list">
            {approvals.map((a) => (
              <li key={a.id}>
                <div className="flex flex-wrap justify-between gap-2">
                  <strong>{a.title}</strong>
                  <Badge tone={QUEUE_TONE[a.queue]}>{a.queue}</Badge>
                </div>
                <p className="eds-type-small text-[var(--eds-muted)]">
                  {a.category} · {a.risk} · {a.aiAgent}
                </p>
                <p className="eds-type-small">{a.detail}</p>
              </li>
            ))}
          </ul>
        </Card>

        {/* SECTION 5 — Risk Dashboard */}
        <Card aria-label="Risk Dashboard">
          <div className="gov-section-head">
            <h2>Risk Dashboard</h2>
          </div>
          <div className="gov-risks">
            {gov.risks.map((r) => (
              <div key={r.id} className={`gov-risk is-${r.tone}`}>
                <strong>{r.label}</strong>
                <Badge tone={r.tone === "risk" ? "danger" : r.tone === "warn" ? "warning" : "success"}>
                  {r.score}
                </Badge>
                <p className="eds-type-small text-[var(--eds-muted)]">{r.detail}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 6 — AI Governance */}
        <Card aria-label="AI Governance">
          <div className="gov-section-head">
            <h2>AI Governance</h2>
            <Link to="/platform-builder/ai-team" className="eds-type-small text-[var(--eds-primary)]">
              AI Team →
            </Link>
          </div>
          <div className="gov-ai-grid">
            {gov.aiGovernance.map((a) => (
              <div key={a.id} className="gov-ai">
                <strong>{a.name}</strong>
                <span className="eds-type-small">Autonomy L{a.autonomyLevel}</span>
                <span className="eds-type-small">Perms: {a.permissions.join(", ")}</span>
                <Badge tone={a.policyViolations ? "danger" : "success"}>
                  Violations {a.policyViolations}
                </Badge>
                <Badge>Confidence {a.confidence}%</Badge>
                <Badge tone={a.humanOverrides ? "warning" : "default"}>
                  Overrides {a.humanOverrides}
                </Badge>
                <p className="eds-type-small text-[var(--eds-muted)]">
                  Last: {(a.lastDecisions.length ? a.lastDecisions : ["—"]).join(" · ")}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 4 — Enterprise Audit Timeline */}
        <Card aria-label="Enterprise Audit Timeline">
          <div className="gov-section-head">
            <h2>Enterprise Audit Timeline</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Who · What · When · Why · AI / Human / Workflow / API
            </span>
          </div>
          <ul className="gov-audit">
            {gov.auditTimeline.map((e) => (
              <li key={e.id}>
                <div>
                  <Badge>{e.source}</Badge>
                  <p className="eds-type-small text-[var(--eds-muted)]">
                    {new Date(e.when).toLocaleString()}
                  </p>
                </div>
                <div>
                  <strong className="eds-type-small">{e.what}</strong>
                  <p className="eds-type-small">
                    Who: {e.who} · Why: {e.why}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

export function GovernanceWidgetCompact() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const user = useAuthStore((s) => s.user);
  const gov = useMemo(
    () =>
      deriveGovernance(snapshot, {
        notifications,
        roleId: user?.roleId || first.roleId,
        permissions: user?.permissions,
      }),
    [snapshot, notifications, user?.roleId, user?.permissions, first.roleId],
  );

  return (
    <Card title="Governance" className="gov-mc-compact" aria-label="Governance Widget">
      <div className="gov-mc-row">
        <Badge tone="success">Audit {gov.compliance.auditScore}</Badge>
        <Badge>Security {gov.compliance.securityScore}</Badge>
        <Badge tone="success">{gov.compliance.compliancePct}%</Badge>
      </div>
      <div className="gov-mc-row">
        {gov.risks.slice(0, 3).map((r) => (
          <Badge key={r.id} tone={r.tone === "risk" ? "danger" : r.tone === "warn" ? "warning" : "default"}>
            {r.kind} {r.score}
          </Badge>
        ))}
      </div>
      <p className="eds-type-small text-[var(--eds-muted)] mb-2">
        Pending approvals:{" "}
        {gov.approvalQueue.filter((a) => a.queue === "pending" || a.queue === "critical").length}
      </p>
      <Link to="/platform-builder/governance" className="eds-type-small text-[var(--eds-primary)]">
        Governance Center →
      </Link>
    </Card>
  );
}
