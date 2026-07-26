/**
 * Predictive Intelligence & Scenario Simulator UI — Sprint 33.4.
 * Forecast layer over EI / Twin / Fabric / Runtime — no new Engines.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { derivePredictive, type WhatIfScenario } from "./derivePredictive";

const SEV_TONE = {
  low: "default" as const,
  medium: "warning" as const,
  high: "danger" as const,
};

export function PredictiveIntelligencePage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const pred = useMemo(() => derivePredictive(snapshot, notifications), [snapshot, notifications]);
  const [scenarioId, setScenarioId] = useState(pred.scenarios[0]?.id || "grow_sales");
  const scenario: WhatIfScenario =
    pred.scenarios.find((s) => s.id === scenarioId) || pred.scenarios[0]!;

  return (
    <WorkspaceLayout>
      <div className="pred-page" data-testid="predictive-intelligence">
        <header className="pred-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">Predictive Intelligence · Sprint 33.4</p>
            <h1 className="pred-title">Predictive Intelligence</h1>
            <p className="eds-type-body">
              Не только текущее состояние — прогнозы KPI, очередей, AI и сценарии What If.
            </p>
          </div>
          <div className="pred-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Twin →
            </Link>
            <Link to="/platform-builder/runtime" className="eds-type-small text-[var(--eds-primary)]">
              Runtime →
            </Link>
            <Link to="/platform-builder/data-fabric" className="eds-type-small text-[var(--eds-primary)]">
              Data Fabric →
            </Link>
          </div>
        </header>

        {/* SECTION 5 — Executive Forecast */}
        <Card className="pred-exec" aria-label="Executive Forecast">
          <div className="pred-section-head">
            <h2>Executive Forecast</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">сегодня · риски · KPI</span>
          </div>
          <div className="pred-exec-grid">
            <ExecCol title="Вероятнее всего сегодня" items={pred.executive.likelyToday} />
            <ExecCol title="Требует внимания" items={pred.executive.needsAttention} tone="warn" />
            <ExecCol title="Риски возрастают" items={pred.executive.risingRisks} tone="risk" />
            <ExecCol title="KPI изменятся" items={pred.executive.kpiChanges.slice(0, 4)} tone="kpi" />
          </div>
        </Card>

        {/* SECTION 1 — Predictive Dashboard */}
        <Card aria-label="Predictive Dashboard">
          <div className="pred-section-head">
            <h2>Predictive Dashboard</h2>
          </div>
          <div className="pred-forecast-grid">
            {pred.forecasts.map((f) => (
              <div key={f.id} className={`pred-forecast pred-forecast--${f.tone}`}>
                <span className="pred-forecast-label">{f.label}</span>
                <strong>
                  {f.current}
                  <span className="pred-arrow">→</span>
                  {f.forecast}
                  <em> {f.unit}</em>
                </strong>
                <Badge tone={f.tone === "risk" ? "danger" : f.tone === "up" ? "success" : "default"}>
                  {f.deltaPct >= 0 ? "+" : ""}
                  {f.deltaPct}%
                </Badge>
                <p className="eds-type-small text-[var(--eds-muted)]">{f.detail}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 2 — Scenario Simulator */}
        <Card aria-label="Scenario Simulator">
          <div className="pred-section-head">
            <h2>Scenario Simulator</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">What If · без Prediction Engine</span>
          </div>
          <div className="pred-scenario-tabs">
            {pred.scenarios.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`pred-chip${scenarioId === s.id ? " is-on" : ""}`}
                onClick={() => {
                  setScenarioId(s.id);
                  void telemetry.userActivity(`pred_scenario:${s.id}`);
                }}
              >
                {s.title}
              </button>
            ))}
          </div>
          <div className="pred-scenario-body">
            <p>
              <strong>{scenario.action}</strong>
              <span className="pred-flow"> ↓ </span>
              {scenario.effect}
            </p>
            <div className="pred-scenario-cols">
              <div>
                <h3>Импакт</h3>
                <ul>
                  {scenario.impacts.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3>Риски</h3>
                <ul>
                  {scenario.risks.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
            </div>
            <p className="pred-reco">
              <strong>Рекомендация:</strong> {scenario.recommendation}
            </p>
          </div>
        </Card>

        <div className="pred-split">
          {/* SECTION 3 — Risk */}
          <Card aria-label="Risk Detection">
            <div className="pred-section-head">
              <h2>Risk Detection</h2>
            </div>
            <ul className="pred-signal-list">
              {pred.risks.map((r) => (
                <li key={r.id}>
                  <div className="pred-signal-top">
                    <strong>{r.title}</strong>
                    <Badge tone={SEV_TONE[r.severity]}>{r.severity}</Badge>
                  </div>
                  <p className="eds-type-small text-[var(--eds-muted)]">{r.detail}</p>
                  {r.route ? (
                    <Link to={r.route} className="eds-type-small text-[var(--eds-primary)]">
                      Open →
                    </Link>
                  ) : null}
                </li>
              ))}
            </ul>
          </Card>

          {/* SECTION 4 — Opportunity */}
          <Card aria-label="Opportunity Detection">
            <div className="pred-section-head">
              <h2>Opportunity Detection</h2>
            </div>
            <ul className="pred-signal-list">
              {pred.opportunities.map((o) => (
                <li key={o.id}>
                  <div className="pred-signal-top">
                    <strong>{o.title}</strong>
                    <Badge tone="success">{o.kind}</Badge>
                  </div>
                  <p className="eds-type-small text-[var(--eds-muted)]">{o.detail}</p>
                  {o.route ? (
                    <Link to={o.route} className="eds-type-small text-[var(--eds-primary)]">
                      Open →
                    </Link>
                  ) : null}
                </li>
              ))}
            </ul>
          </Card>
        </div>

        {/* SECTION 6 — Twin preview */}
        <Card aria-label="Digital Twin forecasts">
          <div className="pred-section-head">
            <h2>Digital Twin Integration</h2>
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Открыть Twin →
            </Link>
          </div>
          <div className="pred-zones">
            {pred.twinZones.map((z) => (
              <div key={z.id} className={`pred-zone pred-zone--${z.tone}`}>
                <strong>{z.label}</strong>
                <span>{z.detail}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

function ExecCol({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone?: "warn" | "risk" | "kpi";
}) {
  return (
    <div className={`pred-exec-col${tone ? ` pred-exec-col--${tone}` : ""}`}>
      <h3>{title}</h3>
      <ul>
        {items.map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
    </div>
  );
}

export function PredictiveStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const pred = useMemo(() => derivePredictive(snapshot, notifications), [snapshot, notifications]);
  const top = pred.forecasts[0];
  const highRisks = pred.risks.filter((r) => r.severity === "high").length;

  return (
    <div className="pred-strip" aria-label="Predictive Intelligence">
      <span className="pred-strip-label">Predictive</span>
      {top ? (
        <Badge tone={top.tone === "risk" ? "danger" : "success"}>
          KPI {top.current}→{top.forecast}
        </Badge>
      ) : null}
      {highRisks ? <Badge tone="danger">{highRisks} risks</Badge> : <Badge tone="success">stable</Badge>}
      <Link
        to="/platform-builder/predictive"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("pred_open")}
      >
        Forecast →
      </Link>
    </div>
  );
}

/** Compact Mission Control / Dashboard widget. */
export function PredictiveWidgetCompact() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const pred = useMemo(() => derivePredictive(snapshot, notifications), [snapshot, notifications]);

  return (
    <Card title="Predictive Widget" className="pred-mc-compact" aria-label="Predictive Widget">
      <ul className="pred-widget-list">
        {pred.executive.likelyToday.slice(0, 2).map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
      <div className="pred-mc-row">
        {pred.forecasts.slice(0, 3).map((f) => (
          <Badge key={f.id} tone={f.tone === "risk" ? "danger" : f.tone === "up" ? "success" : "default"}>
            {f.id} {f.forecast}
          </Badge>
        ))}
        {pred.executive.risingRisks[0] && pred.executive.risingRisks[0] !== "Риски на контроле" ? (
          <Badge tone="danger">risk</Badge>
        ) : (
          <Badge tone="success">ok</Badge>
        )}
      </div>
      <Link to="/platform-builder/predictive" className="eds-type-small text-[var(--eds-primary)]">
        Predictive Intelligence →
      </Link>
    </Card>
  );
}
