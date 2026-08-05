/**
 * Enterprise Digital Twin UI — Sprint 33.0.
 * Living org mirror over live-ops / City / EI / Workflows.
 * No new AI Core / Dashboard / Workspace / Graph Engine.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useAuthStore } from "@/auth/authStore";
import { telemetry } from "@/integrations/telemetry";
import {
  deriveEnterpriseTwin,
  RELATIONSHIP_CHAIN,
  type TwinNode,
  type TwinNodeKind,
} from "./deriveTwin";
import { deriveIntegrationHub } from "@/enterprise-integrations/deriveIntegrations";
import { deriveRuntime } from "@/ai-runtime/deriveRuntime";
import { deriveDataFabric } from "@/enterprise-data-fabric/deriveFabric";
import { derivePredictive } from "@/predictive-intelligence/derivePredictive";
import { deriveAutonomy } from "@/autonomous-enterprise/deriveAutonomy";

const KIND_LABEL: Record<TwinNodeKind, string> = {
  department: "Подразделение",
  ai: "AI Team",
  people: "Сотрудники",
  process: "Процесс",
  document: "Документы",
  crm: "CRM",
  ecosystem: "Экосистема",
  integration: "Интеграция",
};

const SOURCE_LABEL = {
  workflow: "Workflow",
  ai: "AI",
  crm: "CRM",
  knowledge: "Knowledge",
  documents: "Documents",
  system: "System",
} as const;

export function EnterpriseTwinPage({ showStudioLink = true }: { showStudioLink?: boolean }) {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const ws = useWorkspaceStore((s) => s.workspace);
  const user = useAuthStore((s) => s.user);
  const [selectedId, setSelectedId] = useState<string | null>("ai_team");
  const [filter, setFilter] = useState<TwinNodeKind | "all">("all");

  const company = first.companyName || ws.company || "Enterprise";
  const twin = useMemo(
    () =>
      deriveEnterpriseTwin(snapshot, {
        company,
        notifications,
        roleId: user?.roleId || first.roleId,
      }),
    [snapshot, company, notifications, user?.roleId, first.roleId],
  );

  const intTwin = useMemo(() => deriveIntegrationHub(snapshot).twin, [snapshot]);
  const rtTwin = useMemo(() => deriveRuntime(snapshot, notifications).twin, [snapshot, notifications]);
  const fabricExec = useMemo(
    () => deriveDataFabric(snapshot, { company, notifications, roleId: user?.roleId || first.roleId }).executive,
    [snapshot, company, notifications, user?.roleId, first.roleId],
  );
  const predZones = useMemo(
    () => derivePredictive(snapshot, notifications).twinZones,
    [snapshot, notifications],
  );
  const autoTwin = useMemo(
    () => deriveAutonomy(snapshot, { roleId: user?.roleId || first.roleId, notifications }).twin,
    [snapshot, user?.roleId, first.roleId, notifications],
  );

  const nodes = useMemo(
    () => (filter === "all" ? twin.nodes : twin.nodes.filter((n) => n.kind === filter)),
    [twin.nodes, filter],
  );

  const selected: TwinNode | null =
    twin.nodes.find((n) => n.id === selectedId) ||
    (selectedId ? { id: selectedId, kind: "crm", label: selectedId, detail: "", heat: 0, status: "idle" } : null);

  const impact = selectedId ? twin.impacts[selectedId] : null;

  function select(id: string) {
    setSelectedId(id);
    void telemetry.userActivity(`twin_select:${id}`);
  }

  return (
    <WorkspaceLayout>
      <div className="etwin-page" data-testid="enterprise-twin">
        <header className="etwin-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">Digital Twin Home · Sprint 33.0</p>
            <h1 className="etwin-title">{company}</h1>
            <p className="eds-type-body">
              Организация как единая живая система — подразделения, AI, процессы, CRM, Knowledge и интеграции.
            </p>
          </div>
          <div className="etwin-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Link to="/enterprise-city" className="eds-type-small text-[var(--eds-primary)]">
              City →
            </Link>
            <Link to="/platform-builder/mission-control" className="eds-type-small text-[var(--eds-primary)]">
              Mission Control →
            </Link>
            {showStudioLink ? (
              <Link to="/platform-builder/digital-twin?studio=1" className="eds-type-small text-[var(--eds-primary)]">
                Twin Studio →
              </Link>
            ) : null}
            <Link to="/platform-builder/integrations" className="eds-type-small text-[var(--eds-primary)]">
              Integrations →
            </Link>
            <Link to="/platform-builder/runtime" className="eds-type-small text-[var(--eds-primary)]">
              Runtime →
            </Link>
            <Link to="/platform-builder/data-fabric" className="eds-type-small text-[var(--eds-primary)]">
              Data Fabric →
            </Link>
            <Link to="/platform-builder/predictive" className="eds-type-small text-[var(--eds-primary)]">
              Predictive →
            </Link>
            <Link to="/platform-builder/autonomy" className="eds-type-small text-[var(--eds-primary)]">
              Autonomy →
            </Link>
            <Link to="/platform-builder/learning" className="eds-type-small text-[var(--eds-primary)]">
              Learning →
            </Link>
            <Link to="/platform-builder/okr" className="eds-type-small text-[var(--eds-primary)]">
              OKR →
            </Link>
            <Link to="/platform-builder/governance" className="eds-type-small text-[var(--eds-primary)]">
              Governance →
            </Link>
          </div>
        </header>

        {/* Sprint 33.1 — external systems in Twin */}
        <Card className="etwin-impact" aria-label="Connected integrations">
          <div className="etwin-section-head">
            <h2>External Systems</h2>
            <Link to="/platform-builder/integrations" className="eds-type-small text-[var(--eds-primary)]">
              Integration Hub →
            </Link>
          </div>
          <div className="etwin-exec-grid">
            <ExecCol title="Подключены" items={intTwin.connectedSystems.slice(0, 6)} tone="ok" />
            <ExecCol title="Процессы" items={intTwin.processesUsing.slice(0, 6)} />
            <ExecCol title="AI" items={intTwin.aiUsing.slice(0, 6)} tone="ai" />
          </div>
        </Card>

        {/* Sprint 33.2 — live runtime in Twin */}
        <Card className="etwin-impact" aria-label="Live runtime">
          <div className="etwin-section-head">
            <h2>Live Runtime</h2>
            <Link to="/platform-builder/runtime" className="eds-type-small text-[var(--eds-primary)]">
              Runtime Center →
            </Link>
          </div>
          <div className="etwin-exec-grid">
            <ExecCol
              title="Процессы выполняются"
              items={rtTwin.processesRunning.length ? rtTwin.processesRunning : ["Idle"]}
              tone="ok"
            />
            <ExecCol
              title="AI задействованы"
              items={rtTwin.aiInvolved.length ? rtTwin.aiInvolved : ["—"]}
              tone="ai"
            />
            <ExecCol
              title="Интеграции"
              items={rtTwin.integrationsUsed.length ? rtTwin.integrationsUsed : ["—"]}
            />
          </div>
        </Card>

        {/* Sprint 33.3 — data fabric in Twin */}
        <Card className="etwin-impact" aria-label="Data fabric">
          <div className="etwin-section-head">
            <h2>Data Fabric</h2>
            <Link to="/platform-builder/data-fabric" className="eds-type-small text-[var(--eds-primary)]">
              Graph →
            </Link>
          </div>
          <div className="etwin-exec-grid">
            <ExecCol title="Связанные объекты" items={[String(fabricExec.linkedObjects)]} />
            <ExecCol
              title="Проблемные связи"
              items={[String(fabricExec.problemLinks)]}
              tone={fabricExec.problemLinks ? "risk" : "ok"}
            />
            <ExecCol
              title="Недостающие данные"
              items={[String(fabricExec.missingData)]}
              tone={fabricExec.missingData ? "risk" : "ok"}
            />
          </div>
        </Card>

        {/* Sprint 33.4 — predictive zones on Twin */}
        <Card className="etwin-impact" aria-label="Predictive zones">
          <div className="etwin-section-head">
            <h2>Predictive Zones</h2>
            <Link to="/platform-builder/predictive" className="eds-type-small text-[var(--eds-primary)]">
              Forecast →
            </Link>
          </div>
          <div className="etwin-nodes">
            {predZones.map((z) => (
              <div
                key={z.id}
                className={`etwin-node etwin-node--${z.tone === "risk" || z.tone === "bottleneck" ? "risk" : z.tone === "active" ? "active" : "idle"}`}
              >
                <span className="etwin-node-kind">{z.tone}</span>
                <strong>{z.label}</strong>
                <span className="eds-type-small">{z.detail}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Sprint 33.5 — autonomy on Twin */}
        <Card className="etwin-impact" aria-label="Autonomy twin">
          <div className="etwin-section-head">
            <h2>Autonomy</h2>
            <Link to="/platform-builder/autonomy" className="eds-type-small text-[var(--eds-primary)]">
              Center →
            </Link>
          </div>
          <div className="etwin-exec-grid">
            <ExecCol
              title="Автономные процессы"
              items={autoTwin.autonomousProcesses.slice(0, 4)}
              tone="ok"
            />
            <ExecCol
              title="Ожидают согласования"
              items={autoTwin.pendingApprovals.length ? autoTwin.pendingApprovals.slice(0, 4) : ["—"]}
              tone="risk"
            />
            <ExecCol
              title="Критические решения"
              items={autoTwin.criticalDecisions.length ? autoTwin.criticalDecisions.slice(0, 4) : ["—"]}
              tone="risk"
            />
            <ExecCol
              title="Уровень по отделам"
              items={autoTwin.departmentLevels.slice(0, 4).map((d) => `${d.label}: L${d.level}`)}
            />
          </div>
        </Card>

        {/* SECTION 6 — Executive View */}
        <Card className="etwin-exec" aria-label="Executive View">
          <div className="etwin-section-head">
            <h2>Executive View</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">10 секунд · что происходит в компании</span>
          </div>
          <div className="etwin-exec-grid">
            <ExecCol title="Что происходит" items={twin.executive.happening} />
            <ExecCol title="Работает хорошо" items={twin.executive.working} tone="ok" />
            <ExecCol title="Риски" items={twin.executive.risks.length ? twin.executive.risks : ["Критических рисков нет"]} tone="risk" />
            <ExecCol title="Рост" items={twin.executive.growth.length ? twin.executive.growth : ["Ищите возможности в Marketplace"]} tone="growth" />
            <ExecCol title="AI рекомендует" items={twin.executive.aiRecommends.length ? twin.executive.aiRecommends : ["Открыть Decision Support"]} tone="ai" />
          </div>
        </Card>

        {/* SECTION 2 — Organization Map */}
        <Card className="etwin-map" aria-label="Organization Map">
          <div className="etwin-section-head">
            <h2>Organization Map</h2>
            <div className="etwin-filters">
              {(["all", "department", "ai", "people", "process", "document", "crm", "ecosystem", "integration"] as const).map(
                (k) => (
                  <button
                    key={k}
                    type="button"
                    className={`etwin-chip${filter === k ? " is-on" : ""}`}
                    onClick={() => setFilter(k)}
                  >
                    {k === "all" ? "Все" : KIND_LABEL[k]}
                  </button>
                ),
              )}
            </div>
          </div>
          <div className="etwin-nodes">
            {nodes.map((n) => (
              <button
                key={n.id}
                type="button"
                className={`etwin-node etwin-node--${n.status}${selectedId === n.id ? " is-selected" : ""}`}
                onClick={() => select(n.id)}
              >
                <span className="etwin-node-kind">{KIND_LABEL[n.kind]}</span>
                <strong>{n.label}</strong>
                <span className="eds-type-small">{n.detail}</span>
                <span className="etwin-heat-bar" style={{ ["--h" as string]: `${n.heat}%` }} />
              </button>
            ))}
          </div>
        </Card>

        <div className="etwin-split">
          {/* SECTION 3 — Relationship Graph */}
          <Card className="etwin-graph" aria-label="Relationship Graph">
            <div className="etwin-section-head">
              <h2>Relationship Graph</h2>
              <span className="eds-type-small text-[var(--eds-muted)]">без Graph Engine · цепочка ценности</span>
            </div>
            <ol className="etwin-chain">
              {RELATIONSHIP_CHAIN.map((step, i) => (
                <li key={step.id}>
                  <button
                    type="button"
                    className={`etwin-chain-node${selectedId === step.id ? " is-selected" : ""}`}
                    onClick={() => select(step.id)}
                  >
                    {step.label}
                  </button>
                  {i < RELATIONSHIP_CHAIN.length - 1 ? <span className="etwin-chain-arrow" aria-hidden>↓</span> : null}
                </li>
              ))}
            </ol>
            <p className="eds-type-small text-[var(--eds-muted)]">
              {twin.graph.length} связей · Clients → CRM → Sales → Documents → Finance → Knowledge → AI Team
            </p>
          </Card>

          {/* SECTION 4 — Heatmap */}
          <Card className="etwin-heat" aria-label="Enterprise Heatmap">
            <div className="etwin-section-head">
              <h2>Enterprise Heatmap</h2>
              <span className="eds-type-small text-[var(--eds-muted)]">активность · перегруз · idle</span>
            </div>
            <div className="etwin-heat-grid">
              {twin.heatmap.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className={`etwin-heat-cell etwin-heat-cell--${c.tone}`}
                  onClick={() => select(c.id)}
                  title={c.detail}
                >
                  <strong>{c.label}</strong>
                  <span>{c.heat}</span>
                  <em>{c.detail}</em>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* SECTION 5 — Decision Impact */}
        <Card className="etwin-impact" aria-label="Decision Impact">
          <div className="etwin-section-head">
            <h2>Decision Impact</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              {impact ? impact.objectLabel : "Выберите объект на карте"}
            </span>
          </div>
          {impact ? (
            <div className="etwin-impact-body">
              <p>
                <strong>Если изменить:</strong> {impact.change}
              </p>
              <div className="etwin-impact-cols">
                <div>
                  <h3>Что произойдет</h3>
                  <ul>
                    {impact.effects.map((e) => (
                      <li key={e}>{e}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3>Риски</h3>
                  <ul>
                    {impact.risks.map((e) => (
                      <li key={e}>{e}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <p className="etwin-reco">
                <strong>Рекомендация:</strong> {impact.recommendation}
              </p>
              {selected?.route ? (
                <Link to={selected.route}>
                  <Button
                    onClick={() => void telemetry.userActivity(`twin_open_object:${selected.id}`)}
                  >
                    Открыть модуль →
                  </Button>
                </Link>
              ) : null}
            </div>
          ) : (
            <p className="eds-type-small text-[var(--eds-muted)]">Выберите узел Organization Map или Relationship Graph.</p>
          )}
        </Card>

        {/* SECTION 7 — Enterprise Timeline */}
        <Card className="etwin-timeline" aria-label="Enterprise Timeline">
          <div className="etwin-section-head">
            <h2>Enterprise Timeline</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              Workflow · AI · CRM · Knowledge · Documents
            </span>
          </div>
          <ul className="etwin-tl">
            {twin.timeline.map((t) => (
              <li key={t.id} className={`etwin-tl-item etwin-tl-item--${t.source}`}>
                <time dateTime={t.at}>{new Date(t.at).toLocaleString()}</time>
                <Badge>{SOURCE_LABEL[t.source]}</Badge>
                <strong>{t.title}</strong>
                <span className="eds-type-small">{t.detail}</span>
              </li>
            ))}
          </ul>
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
  tone?: "ok" | "risk" | "growth" | "ai";
}) {
  return (
    <div className={`etwin-exec-col${tone ? ` etwin-exec-col--${tone}` : ""}`}>
      <h3>{title}</h3>
      <ul>
        {(items.length ? items : ["—"]).map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
    </div>
  );
}

/** Compact shell strip — no extra fetch (shared useLiveEnterprise). */
