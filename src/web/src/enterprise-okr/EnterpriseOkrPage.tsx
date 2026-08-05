/**
 * Enterprise Strategy & OKR Intelligence UI — Sprint 33.8.
 * Strategic layer over existing components — no new Strategy Engine.
 */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveOkr, type GoalStatus } from "./deriveOkr";

const STATUS_TONE: Record<GoalStatus, "success" | "warning" | "danger" | "default"> = {
  completed: "success",
  in_progress: "default",
  delayed: "warning",
  at_risk: "danger",
};

const STATUS_LABEL: Record<GoalStatus, string> = {
  completed: "Completed",
  in_progress: "In Progress",
  delayed: "Delayed",
  at_risk: "At Risk",
};

function barClass(status: GoalStatus): string {
  if (status === "completed") return "okr-bar is-done";
  if (status === "at_risk") return "okr-bar is-risk";
  if (status === "delayed") return "okr-bar is-delayed";
  return "okr-bar";
}

export function EnterpriseOkrPage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const ws = useWorkspaceStore((s) => s.workspace);
  const company = first.companyName || ws.company || "Enterprise";

  const okr = useMemo(() => deriveOkr(snapshot, notifications), [snapshot, notifications]);

  return (
    <WorkspaceLayout>
      <div className="okr-page" data-testid="enterprise-okr">
        <header className="okr-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">
              Enterprise Strategy & OKR Intelligence · Sprint 33.8
            </p>
            <h1 className="okr-title">OKR · {company}</h1>
            <p className="eds-type-body">
              Цели организации и сравнение текущей деятельности с ними — поверх EI, Learning, Predictive и
              Control Tower.
            </p>
          </div>
          <div className="okr-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Badge tone="success">{okr.mc.progressAvg}% avg</Badge>
            {okr.mc.riskCount ? (
              <Badge tone="danger">{okr.mc.riskCount} risk</Badge>
            ) : (
              <Badge>on track</Badge>
            )}
            <Link to="/platform-builder/control-tower" className="eds-type-small text-[var(--eds-primary)]">
              Control Tower →
            </Link>
            <Link to="/platform-builder/strategy" className="eds-type-small text-[var(--eds-primary)]">
              Strategy Engine →
            </Link>
            <Link to="/platform-builder/learning" className="eds-type-small text-[var(--eds-primary)]">
              Learning →
            </Link>
          </div>
        </header>

        {/* SECTION 1 — Enterprise Goals */}
        <Card aria-label="Enterprise Goals">
          <div className="okr-section-head">
            <h2>Enterprise Goals</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Revenue · Profit · Sales · Marketing · Production · CS · HR · Ops
            </span>
          </div>
          <div className="okr-goals-grid">
            {okr.goals.map((g) => (
              <div key={g.id} className="okr-goal">
                <div className="okr-goal-top">
                  <strong>{g.label}</strong>
                  <Badge tone={STATUS_TONE[g.status]}>{STATUS_LABEL[g.status]}</Badge>
                </div>
                <p className="eds-type-small text-[var(--eds-muted)]">{g.objective}</p>
                <span className="eds-type-small">
                  KPI: {g.kpi} · Owner: {g.owner}
                </span>
                <span className="eds-type-small">
                  Priority {g.priority.toUpperCase()} · Deadline {g.deadline}
                </span>
                <div className={barClass(g.status)} aria-label={`${g.progress}%`}>
                  <span style={{ width: `${g.progress}%` }} />
                </div>
                <strong className="eds-type-small">{g.progress}% progress</strong>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 2 — OKR Dashboard */}
        <Card aria-label="OKR Dashboard">
          <div className="okr-section-head">
            <h2>OKR Dashboard</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Objective → Key Results → Live KPI → Progress → AI Recommendation
            </span>
          </div>
          <div className="okr-stack">
            {okr.okrCards.map((c) => (
              <div key={c.goalId} className="okr-card">
                <strong>{c.objective}</strong>
                <div className="okr-flow">
                  <div className="okr-flow-step">
                    <span className="eds-type-small text-[var(--eds-muted)]">Objective</span>
                    <span className="eds-type-small">{c.objective}</span>
                  </div>
                  <div className="okr-flow-step">
                    <span className="eds-type-small text-[var(--eds-muted)]">Key Results</span>
                    <span className="eds-type-small">{c.keyResults.join(" · ")}</span>
                  </div>
                  <div className="okr-flow-step">
                    <span className="eds-type-small text-[var(--eds-muted)]">Live KPI</span>
                    <span className="eds-type-small">{c.liveKpi}</span>
                  </div>
                  <div className="okr-flow-step">
                    <span className="eds-type-small text-[var(--eds-muted)]">Current Progress</span>
                    <div className="okr-bar">
                      <span style={{ width: `${c.progress}%` }} />
                    </div>
                    <span className="eds-type-small">{c.progress}%</span>
                  </div>
                  <div className="okr-flow-step">
                    <span className="eds-type-small text-[var(--eds-muted)]">AI Recommendation</span>
                    <span className="eds-type-small">{c.aiRecommendation}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 3 — AI Goal Alignment */}
        <Card aria-label="AI Goal Alignment">
          <div className="okr-section-head">
            <h2>AI Goal Alignment</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Concierge / EI рекомендации → цель · KPI · эффект
            </span>
          </div>
          <div className="okr-align-grid">
            {okr.alignments.map((a) => (
              <div key={a.recommendationId} className="okr-align">
                <strong className="eds-type-small">{a.title}</strong>
                <Badge>{a.goalLabel}</Badge>
                <p className="eds-type-small text-[var(--eds-muted)]">KPI: {a.kpi}</p>
                <p className="eds-type-small">{a.expectedEffect}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 5 — Executive Cockpit */}
        <Card aria-label="Executive Strategy Cockpit">
          <div className="okr-section-head">
            <h2>Executive Cockpit</h2>
            <Link to="/dashboard?mode=executive" className="eds-type-small text-[var(--eds-primary)]">
              Dashboard →
            </Link>
          </div>
          <div className="okr-exec">
            {(
              [
                ["Сегодня", okr.executive.today],
                ["Эта неделя", okr.executive.week],
                ["Этот месяц", okr.executive.month],
                ["Основные отклонения", okr.executive.deviations],
                ["ТОП рисков", okr.executive.topRisks],
                ["ТОП возможностей", okr.executive.topOpportunities],
              ] as const
            ).map(([title, items]) => (
              <div key={title} className="okr-exec-block">
                <strong className="eds-type-small">{title}</strong>
                <ul className="eds-type-small">
                  {(items.length ? items : ["—"]).map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 6 — Scenario Impact */}
        <Card aria-label="Scenario Impact">
          <div className="okr-section-head">
            <h2>Scenario Impact</h2>
            <Link to="/platform-builder/predictive" className="eds-type-small text-[var(--eds-primary)]">
              Predictive →
            </Link>
          </div>
          <div className="okr-scenario-grid">
            {okr.scenarioImpacts.map((s) => (
              <div key={`sc_${s.recommendationId}`} className="okr-scenario">
                <strong className="eds-type-small">{s.title}</strong>
                <Badge>{s.goalLabel}</Badge>
                <p className="eds-type-small">
                  <span className="text-[var(--eds-muted)]">Если выполнить → </span>
                  {s.ifDone}
                </p>
                <p className="eds-type-small">
                  <span className="text-[var(--eds-muted)]">Если не выполнять → </span>
                  {s.ifSkipped}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 7 — Strategy Timeline */}
        <Card aria-label="Strategy Timeline">
          <div className="okr-section-head">
            <h2>Strategy Timeline</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Completed · In Progress · Delayed · At Risk
            </span>
          </div>
          <div className="okr-timeline">
            {okr.timeline
              .slice()
              .sort((a, b) => a.deadline.localeCompare(b.deadline))
              .map((t) => (
                <div key={t.id} className="okr-tl-item">
                  <span className="eds-type-small text-[var(--eds-muted)]">{t.deadline}</span>
                  <div>
                    <strong>{t.label}</strong>
                    <div className={barClass(t.status)}>
                      <span style={{ width: `${t.progress}%` }} />
                    </div>
                  </div>
                  <Badge tone={STATUS_TONE[t.status]}>{STATUS_LABEL[t.status]}</Badge>
                </div>
              ))}
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

export function EnterpriseGoalsWidgetCompact() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const okr = useMemo(() => deriveOkr(snapshot, notifications), [snapshot, notifications]);

  return (
    <Card title="Enterprise Goals" className="okr-mc-compact" aria-label="Enterprise Goals">
      <div className="okr-mc-row">
        <Badge tone="success">Progress {okr.mc.progressAvg}%</Badge>
        <Badge tone={okr.mc.riskCount ? "danger" : "default"}>Risk {okr.mc.riskCount}</Badge>
      </div>
      <p className="eds-type-small text-[var(--eds-muted)] mb-1">Forecast</p>
      <p className="eds-type-small mb-2">{okr.mc.forecast}</p>
      <p className="eds-type-small text-[var(--eds-muted)] mb-1">Blockers</p>
      <ul className="eds-type-small">
        {(okr.mc.blockers.length ? okr.mc.blockers : ["Нет критичных blockers"]).map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <Link to="/platform-builder/okr" className="eds-type-small text-[var(--eds-primary)]">
        OKR Intelligence →
      </Link>
    </Card>
  );
}
