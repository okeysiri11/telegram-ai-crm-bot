/**
 * Autonomous Enterprise & Human-in-the-Loop UI — Sprint 33.5.
 * Managed autonomy over Runtime / Predictive / Workflow — no new Engines.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useAuthStore } from "@/auth/authStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { telemetry } from "@/integrations/telemetry";
import type { ApprovalCategory, AutonomyLevel, RiskLevel } from "./autonomyCatalog";
import { decideApproval, setAutonomyLevel } from "./autonomyState";
import { deriveAutonomy } from "./deriveAutonomy";

const RISK_TONE: Record<RiskLevel, "default" | "success" | "warning" | "danger"> = {
  low: "success",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

export function AutonomousEnterprisePage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const pushNotif = useNotificationStore((s) => s.push);
  const user = useAuthStore((s) => s.user);
  const first = loadFirstEntry();
  const roleId = user?.roleId || first.roleId;
  const [cat, setCat] = useState<ApprovalCategory | "all">("all");
  const [tick, setTick] = useState(0);

  const bundle = useMemo(
    () => deriveAutonomy(snapshot, { roleId, notifications, tick }),
    [snapshot, roleId, notifications, tick],
  );

  const approvals = useMemo(() => {
    if (cat === "all") return bundle.approvals;
    return bundle.approvals.filter((a) => a.category === cat);
  }, [bundle.approvals, cat]);

  function refresh() {
    setTick((t) => t + 1);
  }

  function onLevel(level: AutonomyLevel) {
    setAutonomyLevel(level);
    pushNotif({
      kind: "workflow",
      title: `Autonomy Level → ${level}`,
      body: bundle.levels.find((l) => l.level === level)?.title || "",
    });
    void telemetry.userActivity(`auto_level:${level}`);
    refresh();
  }

  function onDecide(id: string, status: "approved" | "rejected" | "edited") {
    decideApproval(id, status, user?.email || roleId || "User");
    pushNotif({
      kind: "task",
      title: `Approval ${status}`,
      body: id,
    });
    void telemetry.userActivity(`auto_decide:${status}:${id}`);
    refresh();
  }

  return (
    <WorkspaceLayout>
      <div className="auto-page" data-testid="autonomous-enterprise">
        <header className="auto-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">
              Autonomous Enterprise · Human-in-the-Loop · Sprint 33.5
            </p>
            <h1 className="auto-title">Autonomy Center</h1>
            <p className="eds-type-body">
              Управляемая автономность: AI выполняет разрешённое, критичное — только с подтверждением.
            </p>
          </div>
          <div className="auto-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Badge tone="warning">L{bundle.dashboard.level}</Badge>
            <Link to="/platform-builder/runtime" className="eds-type-small text-[var(--eds-primary)]">
              Runtime →
            </Link>
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Twin →
            </Link>
          </div>
        </header>

        {/* SECTION 1 — Dashboard */}
        <div className="auto-dash" aria-label="Autonomy Center">
          <DashCard label="Уровень автономности" value={`L${bundle.dashboard.level}`} detail={bundle.dashboard.levelTitle} />
          <DashCard label="Активные автономные" value={String(bundle.dashboard.activeAutonomous)} tone="ok" />
          <DashCard label="Ожидают подтверждения" value={String(bundle.dashboard.awaitingApproval)} tone="warn" />
          <DashCard label="Завершены автоматически" value={String(bundle.dashboard.completedAuto)} />
          <DashCard label="Требуют вмешательства" value={String(bundle.dashboard.needsIntervention)} tone="err" />
        </div>

        {/* SECTION 3 — Levels */}
        <Card aria-label="Autonomy Levels">
          <div className="auto-section-head">
            <h2>Autonomy Levels</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">RBAC / Workspace role: {roleId || "user"}</span>
          </div>
          <div className="auto-levels">
            {bundle.levels.map((l) => (
              <button
                key={l.level}
                type="button"
                className={`auto-level${bundle.dashboard.level === l.level ? " is-on" : ""}`}
                onClick={() => onLevel(l.level)}
              >
                <strong>Level {l.level}</strong>
                <span>{l.title}</span>
                <em className="eds-type-small">{l.summary}</em>
              </button>
            ))}
          </div>
        </Card>

        {/* SECTION 2 — Approval Center */}
        <Card aria-label="Approval Center">
          <div className="auto-section-head">
            <h2>Approval Center</h2>
          </div>
          <div className="auto-filters">
            <button type="button" className={`auto-chip${cat === "all" ? " is-on" : ""}`} onClick={() => setCat("all")}>
              Все
            </button>
            {bundle.categories.map((c) => (
              <button
                key={c.id}
                type="button"
                className={`auto-chip${cat === c.id ? " is-on" : ""}`}
                onClick={() => setCat(c.id)}
              >
                {c.label}
              </button>
            ))}
          </div>
          <div className="auto-approvals">
            {approvals.map((a) => (
              <div key={a.id} className="auto-approval">
                <div className="auto-approval-top">
                  <strong>{a.title}</strong>
                  <Badge>{a.category}</Badge>
                  <Badge tone={RISK_TONE[a.risk]}>{a.risk}</Badge>
                  <Badge tone={a.status === "pending" ? "warning" : a.status === "rejected" ? "danger" : "success"}>
                    {a.status}
                  </Badge>
                </div>
                <p>
                  <strong>AI Recommendation:</strong> {a.recommendation}
                </p>
                <p className="eds-type-small text-[var(--eds-muted)]">Причина: {a.reason}</p>
                <p className="eds-type-small">
                  AI: {a.aiAgent} · Workflow: {a.workflow}
                </p>
                {a.status === "pending" ? (
                  <div className="auto-approval-actions">
                    <Button size="sm" onClick={() => onDecide(a.id, "approved")}>
                      Approve
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => onDecide(a.id, "rejected")}>
                      Reject
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => onDecide(a.id, "edited")}>
                      Edit
                    </Button>
                  </div>
                ) : (
                  <p className="eds-type-small text-[var(--eds-muted)]">
                    {a.decidedBy} · {a.decidedAt ? new Date(a.decidedAt).toLocaleString() : ""}
                  </p>
                )}
              </div>
            ))}
          </div>
          <div className="auto-critical">
            <h3>Действия, требующие подтверждения</h3>
            <ul>
              {bundle.criticalActions.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          </div>
        </Card>

        <div className="auto-split">
          {/* SECTION 4 — Journal */}
          <Card aria-label="Decision Journal">
            <div className="auto-section-head">
              <h2>Decision Journal</h2>
            </div>
            <ul className="auto-journal">
              {bundle.journal.map((j) => (
                <li key={j.id}>
                  <time>{new Date(j.at).toLocaleString()}</time>
                  <strong>{j.action}</strong>
                  <span className="eds-type-small">
                    {j.initiator} · {j.aiAgent} · {j.workflow}
                  </span>
                  <Badge tone={j.userConfirmation === "rejected" ? "danger" : j.userConfirmation === "auto" ? "success" : "default"}>
                    {j.userConfirmation}
                  </Badge>
                  <span className="eds-type-small text-[var(--eds-muted)]">→ {j.result}</span>
                </li>
              ))}
            </ul>
          </Card>

          {/* SECTION 5 — Governance */}
          <Card aria-label="Executive Governance">
            <div className="auto-section-head">
              <h2>Executive Governance</h2>
            </div>
            <div className="auto-gov-grid">
              <GovStat label="Решений AI" value={String(bundle.governance.aiDecisions)} />
              <GovStat label="Подтвердил пользователь" value={String(bundle.governance.userApproved)} />
              <GovStat label="Отклонено" value={String(bundle.governance.userRejected)} />
              <GovStat label="Экономия времени" value={`${bundle.governance.timeSavedMin} мин`} />
            </div>
            <h3 className="auto-sub">Автономность по отделам</h3>
            <ul className="auto-dept">
              {bundle.governance.byDepartment.map((d) => (
                <li key={d.id}>
                  <span>{d.label}</span>
                  <div className="auto-bar">
                    <div style={{ width: `${d.autonomyPct}%` }} />
                  </div>
                  <em>{d.autonomyPct}%</em>
                </li>
              ))}
            </ul>
          </Card>
        </div>

        {/* SECTION 6 — Twin link */}
        <Card aria-label="Digital Twin autonomy">
          <div className="auto-section-head">
            <h2>Digital Twin</h2>
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Открыть Twin →
            </Link>
          </div>
          <div className="auto-twin-grid">
            <div>
              <h3>Автономные процессы</h3>
              <ul>
                {bundle.twin.autonomousProcesses.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Ожидают согласования</h3>
              <ul>
                {(bundle.twin.pendingApprovals.length ? bundle.twin.pendingApprovals : ["—"]).map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Критические решения</h3>
              <ul>
                {(bundle.twin.criticalDecisions.length ? bundle.twin.criticalDecisions : ["—"]).map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Уровень по подразделениям</h3>
              <ul>
                {bundle.twin.departmentLevels.map((d) => (
                  <li key={d.label}>
                    {d.label}: L{d.level}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

function DashCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: "ok" | "warn" | "err";
}) {
  return (
    <div className={`auto-dash-card${tone ? ` auto-dash-card--${tone}` : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <em className="eds-type-small">{detail}</em> : null}
    </div>
  );
}

function GovStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="auto-gov-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function AutonomyStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const bundle = useMemo(
    () => deriveAutonomy(snapshot, { roleId: first.roleId, notifications }),
    [snapshot, first.roleId, notifications],
  );
  return (
    <div className="auto-strip" aria-label="Autonomy">
      <span className="auto-strip-label">Autonomy</span>
      <Badge>L{bundle.dashboard.level}</Badge>
      <Badge tone="warning">{bundle.dashboard.awaitingApproval} pending</Badge>
      {bundle.dashboard.needsIntervention ? (
        <Badge tone="danger">{bundle.dashboard.needsIntervention} alert</Badge>
      ) : (
        <Badge tone="success">ok</Badge>
      )}
      <Link
        to="/platform-builder/autonomy"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("auto_open")}
      >
        Center →
      </Link>
    </div>
  );
}

/** Compact Mission Control widget. */
export function AutonomousWidgetCompact() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const bundle = useMemo(
    () => deriveAutonomy(snapshot, { roleId: first.roleId, notifications }),
    [snapshot, first.roleId, notifications],
  );

  return (
    <Card title="Autonomous Widget" className="auto-mc-compact" aria-label="Autonomous Widget">
      <div className="auto-mc-row">
        <Badge tone="warning">{bundle.dashboard.awaitingApproval} Pending Approvals</Badge>
        <Badge tone="success">{bundle.governance.aiDecisions} AI Decisions Today</Badge>
        <Badge tone={bundle.dashboard.needsIntervention ? "danger" : "default"}>
          {bundle.dashboard.needsIntervention || bundle.twin.criticalDecisions.length} Critical
        </Badge>
      </div>
      <Link to="/platform-builder/autonomy" className="eds-type-small text-[var(--eds-primary)]">
        Autonomy Center →
      </Link>
    </Card>
  );
}
