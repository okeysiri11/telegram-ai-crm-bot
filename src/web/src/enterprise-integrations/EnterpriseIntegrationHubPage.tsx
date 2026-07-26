/**
 * Enterprise Integration Hub UI — Sprint 33.1.
 * Unified control of external integrations — no new Engine / Gateway.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { BuilderStepNav } from "../../platform-builder/framework/BuilderStepNav";
import { ProgressIndicator } from "../../platform-builder/framework/ProgressIndicator";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import {
  ALL_INTEGRATIONS,
  INTEGRATION_CATEGORIES,
  getIntegration,
  integrationsByCategory,
  type IntegrationCategory,
  type IntegrationDef,
  type IntegrationStatus,
} from "./integrationCatalog";
import { connectIntegration, syncIntegration } from "./connectionState";
import { deriveIntegrationHub } from "./deriveIntegrations";

const STATUS_TONE: Record<IntegrationStatus, "default" | "success" | "warning" | "danger"> = {
  active: "success",
  needs_setup: "warning",
  error: "danger",
  idle: "default",
  draft: "warning",
};

const STATUS_LABEL: Record<IntegrationStatus, string> = {
  active: "Активна",
  needs_setup: "Требует настройки",
  error: "Ошибка",
  idle: "Idle",
  draft: "Draft",
};

export function EnterpriseIntegrationHubPage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const pushNotif = useNotificationStore((s) => s.push);
  const [cat, setCat] = useState<IntegrationCategory | "all">("all");
  const [selectedId, setSelectedId] = useState<string | null>("telegram");
  const [wizardId, setWizardId] = useState<string | null>(null);
  const [wizardStep, setWizardStep] = useState(0);
  const [tick, setTick] = useState(0);

  const bundle = useMemo(() => {
    void tick;
    return deriveIntegrationHub(snapshot);
  }, [snapshot, tick]);

  const list = useMemo(() => {
    const ids = new Set(integrationsByCategory(cat).map((i) => i.id));
    return bundle.rows.filter((r) => ids.has(r.id));
  }, [bundle.rows, cat]);

  const selected = selectedId ? getIntegration(selectedId) : null;
  const selectedRow = bundle.rows.find((r) => r.id === selectedId);
  const wizardDef = wizardId ? getIntegration(wizardId) : null;

  function refresh() {
    setTick((t) => t + 1);
  }

  function openWizard(def: IntegrationDef) {
    setWizardId(def.id);
    setWizardStep(0);
    setSelectedId(def.id);
    void telemetry.userActivity(`int_wizard:${def.id}`);
  }

  function finishWizard() {
    if (!wizardId) return;
    connectIntegration(wizardId);
    pushNotif({
      kind: "workflow",
      title: `Интеграция подключена: ${getIntegration(wizardId)?.title}`,
      body: "Connection Wizard завершён · статус active",
    });
    setWizardId(null);
    refresh();
  }

  function onSync(id: string) {
    syncIntegration(id);
    pushNotif({
      kind: "in_app",
      title: `Синхронизация: ${getIntegration(id)?.title}`,
      body: "Последняя синхронизация обновлена",
    });
    void telemetry.userActivity(`int_sync:${id}`);
    refresh();
  }

  return (
    <WorkspaceLayout>
      <div className="eih-page" data-testid="enterprise-integration-hub">
        <header className="eih-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">Enterprise Integration Hub · Sprint 33.1</p>
            <h1 className="eih-title">Integrations</h1>
            <p className="eds-type-body">
              Единая точка управления внешними интеграциями — Communication, Business, Developer.
            </p>
          </div>
          <div className="eih-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Twin →
            </Link>
            <Link to="/platform-builder/solution-hub" className="eds-type-small text-[var(--eds-primary)]">
              Marketplace →
            </Link>
          </div>
        </header>

        {/* SECTION 1 — Dashboard */}
        <div className="eih-dash" aria-label="Integration Dashboard">
          <DashCard label="Активные" value={String(bundle.dashboard.active)} tone="ok" />
          <DashCard label="Требуют настройки" value={String(bundle.dashboard.needsSetup)} tone="warn" />
          <DashCard label="Ошибки подключения" value={String(bundle.dashboard.errors)} tone="err" />
          <DashCard
            label="Последняя синхронизация"
            value={
              bundle.dashboard.lastSyncAt
                ? new Date(bundle.dashboard.lastSyncAt).toLocaleString()
                : "—"
            }
          />
          <DashCard label="Статус" value={bundle.dashboard.statusSummary} />
        </div>

        <div className="eih-filters">
          {INTEGRATION_CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`eih-chip${cat === c.id ? " is-on" : ""}`}
              onClick={() => setCat(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* SECTION 2–4 cards */}
        <div className="eih-grid">
          {list.map((row) => {
            const def = getIntegration(row.id)!;
            return (
              <Card
                key={row.id}
                className={`eih-card${selectedId === row.id ? " is-selected" : ""}`}
              >
                <button type="button" className="eih-card-btn" onClick={() => setSelectedId(row.id)}>
                  <div className="eih-card-top">
                    <strong>{row.title}</strong>
                    <Badge tone={STATUS_TONE[row.status]}>{STATUS_LABEL[row.status]}</Badge>
                  </div>
                  <p className="eds-type-small text-[var(--eds-muted)]">{def.description}</p>
                  <span className="eih-cat">{def.category}</span>
                </button>
                <div className="eih-card-actions">
                  <Button size="sm" variant="secondary" onClick={() => openWizard(def)}>
                    Подключить
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onSync(row.id)}>
                    Sync
                  </Button>
                  {row.route ? (
                    <Link to={row.route} className="eds-type-small text-[var(--eds-primary)]">
                      Open →
                    </Link>
                  ) : null}
                </div>
              </Card>
            );
          })}
        </div>

        {/* SECTION 5 — Monitor */}
        <Card className="eih-monitor" aria-label="Integration Monitor">
          <div className="eih-section-head">
            <h2>Integration Monitor</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              статус · sync · операции · ошибки · latency
            </span>
          </div>
          <div className="eih-table-wrap">
            <table className="eih-table">
              <thead>
                <tr>
                  <th>Интеграция</th>
                  <th>Статус</th>
                  <th>Последняя синхронизация</th>
                  <th>Операции</th>
                  <th>Ошибки</th>
                  <th>Ответ</th>
                </tr>
              </thead>
              <tbody>
                {bundle.rows.map((r) => (
                  <tr
                    key={r.id}
                    className={selectedId === r.id ? "is-selected" : ""}
                    onClick={() => setSelectedId(r.id)}
                  >
                    <td>{r.title}</td>
                    <td>
                      <Badge tone={STATUS_TONE[r.status]}>{STATUS_LABEL[r.status]}</Badge>
                    </td>
                    <td>{r.lastSyncAt ? new Date(r.lastSyncAt).toLocaleString() : "—"}</td>
                    <td>{r.operations}</td>
                    <td>{r.errors}</td>
                    <td>{r.latencyMs ? `${r.latencyMs} ms` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* SECTION 6 — Connection Wizard */}
        {wizardDef ? (
          <Card className="eih-wizard" aria-label="Connection Wizard">
            <div className="eih-section-head">
              <h2>Connection Wizard · {wizardDef.title}</h2>
              <Button size="sm" variant="ghost" onClick={() => setWizardId(null)}>
                Закрыть
              </Button>
            </div>
            <ProgressIndicator current={wizardStep} total={wizardDef.wizardSteps.length} />
            <div className="mt-3">
              <BuilderStepNav
                steps={wizardDef.wizardSteps}
                current={wizardStep}
                onChange={setWizardStep}
              />
            </div>
            <p className="mt-3 eds-type-body">
              Шаг: <strong>{wizardDef.wizardSteps[wizardStep]}</strong>
              {wizardDef.healthHint || selectedRow?.hubPath ? (
                <>
                  {" "}
                  · endpoint <code>{wizardDef.healthHint || selectedRow?.hubPath}</code>
                </>
              ) : null}
            </p>
            <p className="eds-type-small text-[var(--eds-muted)]">
              Использует существующий Builder UX (BuilderStepNav / ProgressIndicator). Без нового Engine.
            </p>
            <div className="eih-wizard-actions">
              <Button
                variant="secondary"
                disabled={wizardStep <= 0}
                onClick={() => setWizardStep((s) => Math.max(0, s - 1))}
              >
                Назад
              </Button>
              {wizardStep < wizardDef.wizardSteps.length - 1 ? (
                <Button onClick={() => setWizardStep((s) => s + 1)}>Далее</Button>
              ) : (
                <Button onClick={finishWizard}>Активировать</Button>
              )}
            </div>
          </Card>
        ) : null}

        {/* SECTION 7 — Twin link */}
        <Card className="eih-twin" aria-label="Digital Twin integrations">
          <div className="eih-section-head">
            <h2>Enterprise Digital Twin</h2>
            <Link to="/enterprise-twin" className="eds-type-small text-[var(--eds-primary)]">
              Открыть Twin →
            </Link>
          </div>
          <div className="eih-twin-grid">
            <div>
              <h3>Подключённые системы</h3>
              <ul>
                {bundle.twin.connectedSystems.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Процессы используют</h3>
              <ul>
                {bundle.twin.processesUsing.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>AI работают с ними</h3>
              <ul>
                {bundle.twin.aiUsing.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
          </div>
          {selected ? (
            <p className="eds-type-small text-[var(--eds-muted)] mt-2">
              Выбрано: <strong>{selected.title}</strong> · процессы: {selected.processes.join(", ")} ·
              AI: {selected.aiAgents.join(", ")}
            </p>
          ) : null}
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

function DashCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "ok" | "warn" | "err";
}) {
  return (
    <div className={`eih-dash-card${tone ? ` eih-dash-card--${tone}` : ""}`}>
      <span className="eih-dash-label">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function IntegrationHubStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const bundle = useMemo(() => deriveIntegrationHub(snapshot), [snapshot]);
  return (
    <div className="eih-strip" aria-label="Integration Hub">
      <span className="eih-strip-label">Integrations</span>
      <Badge tone="success">{bundle.dashboard.active} active</Badge>
      {bundle.dashboard.needsSetup ? (
        <Badge tone="warning">{bundle.dashboard.needsSetup} setup</Badge>
      ) : null}
      {bundle.dashboard.errors ? (
        <Badge tone="danger">{bundle.dashboard.errors} err</Badge>
      ) : (
        <Badge>ok</Badge>
      )}
      <Link
        to="/platform-builder/integrations"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("int_hub_open")}
      >
        Hub →
      </Link>
    </div>
  );
}

export { ALL_INTEGRATIONS };
