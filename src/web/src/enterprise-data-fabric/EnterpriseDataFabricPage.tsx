/**
 * Enterprise Data Fabric UI — Sprint 33.3.
 * Unified related data model — no new Database / Knowledge Engine.
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
import { KIND_LABEL, type FabricEntityKind } from "./fabricCatalog";
import { deriveDataFabric } from "./deriveFabric";

export function EnterpriseDataFabricPage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const ws = useWorkspaceStore((s) => s.workspace);
  const user = useAuthStore((s) => s.user);
  const [selectedId, setSelectedId] = useState("knowledge");

  const company = first.companyName || ws.company || "Enterprise";
  const fabric = useMemo(
    () =>
      deriveDataFabric(snapshot, {
        company,
        notifications,
        roleId: user?.roleId || first.roleId,
      }),
    [snapshot, company, notifications, user?.roleId, first.roleId],
  );

  const selected = fabric.entities.find((e) => e.id === selectedId) || fabric.entities[0]!;
  const explorer = fabric.explore(selectedId);
  const lineage = fabric.lineage[selectedId];
  const impact = fabric.impact[selectedId];

  function select(id: string) {
    setSelectedId(id);
    void telemetry.userActivity(`fabric_select:${id}`);
  }

  return (
    <WorkspaceLayout>
      <div className="edf-page" data-testid="enterprise-data-fabric">
        <header className="edf-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">Enterprise Data Fabric · Sprint 33.3</p>
            <h1 className="edf-title">Data Fabric</h1>
            <p className="eds-type-body">
              Единая связанная модель данных — Companies, Users, AI, CRM, Documents, Workflows, Knowledge,
              Integrations.
            </p>
          </div>
          <div className="edf-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Link to="/platform-builder/knowledge" className="eds-type-small text-[var(--eds-primary)]">
              Knowledge →
            </Link>
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Twin →
            </Link>
            <Link to="/platform-builder/runtime" className="eds-type-small text-[var(--eds-primary)]">
              Runtime →
            </Link>
          </div>
        </header>

        {/* SECTION 6 — Executive */}
        <div className="edf-exec" aria-label="Executive View">
          <ExecStat label="Связанные объекты" value={String(fabric.executive.linkedObjects)} />
          <ExecStat label="Активные зависимости" value={String(fabric.executive.activeDependencies)} />
          <ExecStat
            label="Проблемные связи"
            value={String(fabric.executive.problemLinks)}
            tone={fabric.executive.problemLinks ? "warn" : "ok"}
          />
          <ExecStat
            label="Недостающие данные"
            value={String(fabric.executive.missingData)}
            tone={fabric.executive.missingData ? "warn" : "ok"}
          />
          <div className="edf-exec-card edf-exec-card--wide">
            <span>Последние изменения</span>
            <ul>
              {(fabric.executive.recentChanges.length ? fabric.executive.recentChanges : ["—"]).map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* SECTION 1 — Enterprise Graph */}
        <Card className="edf-graph" aria-label="Enterprise Graph">
          <div className="edf-section-head">
            <h2>Enterprise Graph</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              {fabric.entities.length} nodes · {fabric.edges.length} links
            </span>
          </div>
          <div className="edf-nodes">
            {fabric.entities.map((e) => (
              <button
                key={e.id}
                type="button"
                className={`edf-node${selectedId === e.id ? " is-selected" : ""}${e.problem ? " is-problem" : ""}${e.missing ? " is-missing" : ""}`}
                onClick={() => select(e.id)}
              >
                <span className="edf-kind">{KIND_LABEL[e.kind as FabricEntityKind]}</span>
                <strong>{e.label}</strong>
                <span className="eds-type-small">{e.detail}</span>
                {e.problem ? <Badge tone="danger">problem</Badge> : null}
                {e.missing ? <Badge tone="warning">missing</Badge> : null}
              </button>
            ))}
          </div>
          <ul className="edf-edges">
            {fabric.edges.slice(0, 12).map((edge) => (
              <li key={edge.id}>
                <button type="button" onClick={() => select(edge.from)}>
                  {fabric.entities.find((x) => x.id === edge.from)?.label || edge.from}
                </button>
                <span> —{edge.label}→ </span>
                <button type="button" onClick={() => select(edge.to)}>
                  {fabric.entities.find((x) => x.id === edge.to)?.label || edge.to}
                </button>
              </li>
            ))}
          </ul>
        </Card>

        <div className="edf-split">
          {/* SECTION 2 — Explorer */}
          <Card aria-label="Relationship Explorer">
            <div className="edf-section-head">
              <h2>Relationship Explorer</h2>
              <Badge>{selected.label}</Badge>
            </div>
            <h3 className="edf-sub">Связанные объекты</h3>
            <ul className="edf-list">
              {explorer.related.map((r) => (
                <li key={r.id}>
                  <button type="button" className="edf-linkish" onClick={() => select(r.id === "twin" ? "company" : r.id)}>
                    {r.label}
                  </button>
                  <span className="eds-type-small text-[var(--eds-muted)]"> · {r.detail}</span>
                  {r.route ? (
                    <Link to={r.route} className="eds-type-small text-[var(--eds-primary)]">
                      {" "}
                      open
                    </Link>
                  ) : null}
                </li>
              ))}
            </ul>
            <h3 className="edf-sub">История изменений</h3>
            <ul className="edf-list">
              {explorer.changeHistory.map((h) => (
                <li key={`${h.entityId}_${h.changedAt}`}>
                  {h.changedBy} · {new Date(h.changedAt).toLocaleString()} · via {h.workflow}
                </li>
              ))}
            </ul>
            <h3 className="edf-sub">Активные процессы</h3>
            <ul className="edf-list">
              {(explorer.activeProcesses.length ? explorer.activeProcesses : ["Idle"]).map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
            <h3 className="edf-sub">AI используют объект</h3>
            <div className="edf-badges">
              {explorer.aiUsing.map((a) => (
                <Badge key={a} tone="success">
                  {a}
                </Badge>
              ))}
            </div>
          </Card>

          {/* SECTION 3 — Lineage + SECTION 5 — Impact */}
          <div className="edf-stack">
            <Card aria-label="Data Lineage">
              <div className="edf-section-head">
                <h2>Data Lineage</h2>
              </div>
              {lineage ? (
                <dl className="edf-dl">
                  <div>
                    <dt>Источник данных</dt>
                    <dd>{lineage.source}</dd>
                  </div>
                  <div>
                    <dt>Кто изменил</dt>
                    <dd>{lineage.changedBy}</dd>
                  </div>
                  <div>
                    <dt>Когда</dt>
                    <dd>{new Date(lineage.changedAt).toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt>Workflow</dt>
                    <dd>{lineage.workflow}</dd>
                  </div>
                  <div>
                    <dt>AI участвовал</dt>
                    <dd>{lineage.aiParticipant}</dd>
                  </div>
                </dl>
              ) : null}
            </Card>

            <Card aria-label="Impact Analysis">
              <div className="edf-section-head">
                <h2>Impact Analysis</h2>
              </div>
              {impact ? (
                <>
                  <h3 className="edf-sub">Зависит от объекта</h3>
                  <ul className="edf-list">
                    {impact.dependsOn.map((d) => (
                      <li key={d}>{d}</li>
                    ))}
                  </ul>
                  <h3 className="edf-sub">Workflow затронуты</h3>
                  <ul className="edf-list">
                    {(impact.workflowsAffected.length ? impact.workflowsAffected : ["—"]).map((w) => (
                      <li key={w}>{w}</li>
                    ))}
                  </ul>
                  <h3 className="edf-sub">AI используют данные</h3>
                  <ul className="edf-list">
                    {impact.aiUsing.map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                  </ul>
                  <h3 className="edf-sub">Интеграции получают</h3>
                  <ul className="edf-list">
                    {(impact.integrationsReceiving.length ? impact.integrationsReceiving : ["—"]).map((i) => (
                      <li key={i}>{i}</li>
                    ))}
                  </ul>
                </>
              ) : null}
              {selected.route ? (
                <Link to={selected.route}>
                  <Button size="sm" variant="secondary" onClick={() => void telemetry.userActivity(`fabric_open:${selected.id}`)}>
                    Открыть модуль →
                  </Button>
                </Link>
              ) : null}
            </Card>
          </div>
        </div>

        {/* SECTION 4 — Knowledge Connections */}
        <Card aria-label="Knowledge Connections">
          <div className="edf-section-head">
            <h2>Knowledge Connections</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">Knowledge → … → Digital Twin</span>
          </div>
          <ol className="edf-chain">
            {fabric.knowledgeChain.map((step, i) => (
              <li key={step.id}>
                <button
                  type="button"
                  className={`edf-chain-node${selectedId === step.id || (step.id === "twin" && selectedId === "company") ? " is-selected" : ""}`}
                  onClick={() => select(step.id === "twin" ? "knowledge" : step.id)}
                >
                  {step.label}
                </button>
                {i < fabric.knowledgeChain.length - 1 ? (
                  <span className="edf-chain-arrow" aria-hidden>
                    ↓
                  </span>
                ) : null}
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

function ExecStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "ok" | "warn";
}) {
  return (
    <div className={`edf-exec-card${tone ? ` edf-exec-card--${tone}` : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function DataFabricOverviewCompact() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const fabric = useMemo(() => deriveDataFabric(snapshot, { notifications }), [snapshot, notifications]);

  return (
    <Card title="Data Fabric Overview" className="edf-mc-compact" aria-label="Data Fabric Overview">
      <div className="edf-mc-row">
        <Badge>{fabric.executive.linkedObjects} objects</Badge>
        <Badge tone="success">{fabric.executive.activeDependencies} deps</Badge>
        {fabric.executive.problemLinks ? (
          <Badge tone="danger">{fabric.executive.problemLinks} problems</Badge>
        ) : (
          <Badge tone="success">links ok</Badge>
        )}
        {fabric.executive.missingData ? (
          <Badge tone="warning">{fabric.executive.missingData} missing</Badge>
        ) : (
          <Badge tone="success">complete</Badge>
        )}
      </div>
      <p className="eds-type-small text-[var(--eds-muted)] mt-2">
        Last: {fabric.executive.recentChanges[0] || "—"}
      </p>
      <Link to="/platform-builder/data-fabric" className="eds-type-small text-[var(--eds-primary)]">
        Data Fabric →
      </Link>
    </Card>
  );
}
