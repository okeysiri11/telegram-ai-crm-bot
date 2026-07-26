/**
 * Enterprise Control Tower UI — Sprint 33.6.
 * Executive home composing existing subsystems — no new Dashboard Engine.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useAuthStore } from "@/auth/authStore";
import { searchIndex } from "../../navigation/managers/searchIndex";
import { telemetry } from "@/integrations/telemetry";
import {
  RuntimeMonitorCompact,
} from "@/ai-runtime";
import { DataFabricOverviewCompact } from "@/enterprise-data-fabric";
import { PredictiveWidgetCompact } from "@/predictive-intelligence";
import { AutonomousWidgetCompact } from "@/autonomous-enterprise";
import { LearningWidgetCompact } from "@/self-learning-enterprise";
import { EnterpriseGoalsWidgetCompact } from "@/enterprise-okr";
import { deriveControlTower } from "./deriveControlTower";

const INC_TONE = {
  error: "danger" as const,
  warning: "warning" as const,
  degraded: "warning" as const,
  overload: "danger" as const,
  info: "default" as const,
};

export function EnterpriseControlTowerPage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const ws = useWorkspaceStore((s) => s.workspace);
  const user = useAuthStore((s) => s.user);
  const company = first.companyName || ws.company || "Enterprise";
  const [q, setQ] = useState("");

  const tower = useMemo(
    () =>
      deriveControlTower(snapshot, {
        company,
        notifications,
        roleId: user?.roleId || first.roleId,
      }),
    [snapshot, company, notifications, user?.roleId, first.roleId],
  );

  const searchHits = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return [];
    return searchIndex
      .list()
      .filter(
        (d) =>
          d.title.toLowerCase().includes(query) ||
          d.tokens.some((t) => t.toLowerCase().includes(query)) ||
          d.category.toLowerCase().includes(query),
      )
      .slice(0, 12);
  }, [q]);

  return (
    <WorkspaceLayout>
      <div className="ect-page" data-testid="enterprise-control-tower">
        <header className="ect-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">Enterprise Control Tower · Sprint 33.6</p>
            <h1 className="ect-title">{company}</h1>
            <p className="eds-type-body">
              Главный экран руководителя — Mission Control, Twin, Runtime, Predictive, Autonomy и экосистемы в одном
              месте.
            </p>
          </div>
          <div className="ect-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Link to="/platform-builder/mission-control" className="eds-type-small text-[var(--eds-primary)]">
              Mission Control →
            </Link>
            <Link to="/dashboard?mode=executive" className="eds-type-small text-[var(--eds-primary)]">
              Dashboard →
            </Link>
          </div>
        </header>

        {/* SECTION 5 — Global Search */}
        <Card aria-label="Global Search">
          <div className="ect-section-head">
            <h2>Global Search</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              users · AI · Workflow · docs · CRM · integrations · orgs
            </span>
          </div>
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Поиск по платформе…"
            aria-label="Control Tower search"
          />
          {searchHits.length ? (
            <ul className="ect-search-hits">
              {searchHits.map((h) => (
                <li key={h.id}>
                  <Link
                    to={h.path}
                    onClick={() => void telemetry.userActivity(`ect_search:${h.id}`)}
                  >
                    {h.title}
                  </Link>
                  <Badge>{h.category}</Badge>
                </li>
              ))}
            </ul>
          ) : q.trim() ? (
            <p className="eds-type-small text-[var(--eds-muted)] mt-2">Ничего не найдено</p>
          ) : null}
        </Card>

        {/* SECTION 1 — Global Overview */}
        <div className="ect-overview" aria-label="Global Overview">
          {tower.overview.map((o) => (
            <Link key={o.id} to={o.route} className={`ect-ov-card ect-ov-card--${o.tone || "ok"}`}>
              <span>{o.label}</span>
              <strong>{o.value}</strong>
              <em>{o.detail}</em>
            </Link>
          ))}
        </div>

        {/* SECTION 3 — Executive Cockpit */}
        <Card aria-label="Executive Cockpit">
          <div className="ect-section-head">
            <h2>Executive Cockpit</h2>
          </div>
          <div className="ect-cockpit">
            {tower.cockpit.map((k) => (
              <Link key={k.id} to={k.route || "/dashboard"} className={`ect-kpi ect-kpi--${k.tone}`}>
                <span>{k.label}</span>
                <strong>{k.value}</strong>
                <em>{k.delta}</em>
              </Link>
            ))}
          </div>
        </Card>

        {/* SECTION 7 — Command Actions */}
        <Card aria-label="Command Actions">
          <div className="ect-section-head">
            <h2>Command Actions</h2>
          </div>
          <div className="ect-commands">
            {tower.commands.map((c) => (
              <Link key={c.id} to={c.route}>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => void telemetry.userActivity(`ect_cmd:${c.id}`)}
                >
                  {c.label}
                </Button>
              </Link>
            ))}
          </div>
        </Card>

        <div className="ect-split">
          {/* SECTION 2 — Operations Wall */}
          <Card aria-label="Operations Wall">
            <div className="ect-section-head">
              <h2>Operations Wall</h2>
            </div>
            <ul className="ect-ops">
              {tower.operations.map((op) => (
                <li key={op.id} className={`ect-ops-item ect-ops-item--${op.kind}`}>
                  <div>
                    <strong>{op.title}</strong>
                    <p className="eds-type-small text-[var(--eds-muted)]">{op.detail}</p>
                  </div>
                  {op.route ? (
                    <Link to={op.route} className="eds-type-small text-[var(--eds-primary)]">
                      Open
                    </Link>
                  ) : null}
                </li>
              ))}
            </ul>
          </Card>

          {/* SECTION 6 — Incident Center */}
          <Card aria-label="Incident Center">
            <div className="ect-section-head">
              <h2>Incident Center</h2>
            </div>
            <ul className="ect-incidents">
              {tower.incidents.map((inc) => (
                <li key={inc.id}>
                  <div className="ect-inc-top">
                    <strong>{inc.title}</strong>
                    <Badge tone={INC_TONE[inc.severity]}>{inc.severity}</Badge>
                  </div>
                  <p className="eds-type-small text-[var(--eds-muted)]">{inc.detail}</p>
                  {inc.route ? (
                    <Link to={inc.route} className="eds-type-small text-[var(--eds-primary)]">
                      Resolve →
                    </Link>
                  ) : null}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        {/* SECTION 4 — Cross Ecosystem */}
        <Card aria-label="Cross Ecosystem Monitor">
          <div className="ect-section-head">
            <h2>Cross Ecosystem Monitor</h2>
          </div>
          <div className="ect-ecos">
            {tower.ecosystems.map((e) => (
              <Link key={e.id} to={e.route} className={`ect-eco${e.ok ? " is-ok" : ""}`}>
                <strong>{e.label}</strong>
                <Badge tone={e.ok ? "success" : "default"}>{e.ok ? "ok" : "idle"}</Badge>
                <span className="eds-type-small">{e.detail}</span>
              </Link>
            ))}
          </div>
        </Card>

        {/* Existing subsystem widgets — composition only */}
        <div className="ect-widgets">
          <RuntimeMonitorCompact />
          <PredictiveWidgetCompact />
          <AutonomousWidgetCompact />
          <DataFabricOverviewCompact />
          <LearningWidgetCompact />
          <EnterpriseGoalsWidgetCompact />
        </div>
      </div>
    </WorkspaceLayout>
  );
}

export function ControlTowerStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const tower = useMemo(
    () => deriveControlTower(snapshot, { company: first.companyName, notifications, roleId: first.roleId }),
    [snapshot, first.companyName, first.roleId, notifications],
  );
  const risks = tower.incidents.filter((i) => i.severity === "error" || i.severity === "overload").length;
  return (
    <div className="ect-strip" aria-label="Control Tower">
      <span className="ect-strip-label">Control Tower</span>
      <Badge tone="success">{tower.overview.find((o) => o.id === "runtime")?.value || "0"} runtime</Badge>
      {risks ? <Badge tone="danger">{risks} incidents</Badge> : <Badge>stable</Badge>}
      <Link
        to="/platform-builder/control-tower"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("ect_open")}
      >
        Tower →
      </Link>
    </div>
  );
}
