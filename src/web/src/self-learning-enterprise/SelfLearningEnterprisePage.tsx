/**
 * Self-Learning Enterprise UI — Sprint 33.7.
 * Continuous optimization over existing layers — no new Learning / Analytics Engine.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveLearning, type LearningRecommendation } from "./deriveLearning";

const CAT_LABEL: Record<LearningRecommendation["category"], string> = {
  workflow: "Workflow",
  ai_team: "AI Team",
  crm: "CRM",
  integrations: "Integrations",
  knowledge: "Knowledge",
  automation: "Automation",
};

const CAT_FILTER: Array<LearningRecommendation["category"] | "all"> = [
  "all",
  "workflow",
  "ai_team",
  "crm",
  "integrations",
  "knowledge",
  "automation",
];

export function SelfLearningEnterprisePage() {
  const { snapshot, busy } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const first = loadFirstEntry();
  const ws = useWorkspaceStore((s) => s.workspace);
  const company = first.companyName || ws.company || "Enterprise";
  const [cat, setCat] = useState<(typeof CAT_FILTER)[number]>("all");

  const learning = useMemo(
    () => deriveLearning(snapshot, notifications),
    [snapshot, notifications],
  );

  const recs =
    cat === "all"
      ? learning.recommendations
      : learning.recommendations.filter((r) => r.category === cat);

  return (
    <WorkspaceLayout>
      <div className="sle-page" data-testid="self-learning-enterprise">
        <header className="sle-hero">
          <div>
            <p className="eds-type-small text-[var(--eds-muted)]">
              Self-Learning Enterprise · Sprint 33.7
            </p>
            <h1 className="sle-title">Learning · {company}</h1>
            <p className="eds-type-body">
              Анализ результатов работы платформы и предложения по непрерывной оптимизации — поверх EI,
              Runtime, Predictive, Workflow и Knowledge.
            </p>
          </div>
          <div className="sle-hero-actions">
            {busy ? <Badge>sync…</Badge> : <Badge tone="success">live</Badge>}
            <Badge tone="success">~{learning.timeSavedMin} мин потенциал</Badge>
            <Link to="/platform-builder/control-tower" className="eds-type-small text-[var(--eds-primary)]">
              Control Tower →
            </Link>
            <Link to="/platform-builder/mission-control" className="eds-type-small text-[var(--eds-primary)]">
              Mission Control →
            </Link>
          </div>
        </header>

        {/* SECTION 1 — Learning Dashboard */}
        <Card aria-label="Learning Dashboard">
          <div className="sle-section-head">
            <h2>Learning Dashboard</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">
              AI · Workflow · скорость · рекомендации · автоматизации
            </span>
          </div>
          <div className="sle-metrics">
            {learning.metrics.map((m) => (
              <div key={m.id} className={`sle-metric is-${m.trend}`}>
                <span className="eds-type-small text-[var(--eds-muted)]">{m.label}</span>
                <strong>
                  {m.value}
                  <span className="eds-type-small"> {m.unit}</span>
                </strong>
                <span className="eds-type-small">{m.detail}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 2 — Workflow Optimization */}
        <Card aria-label="Workflow Optimization">
          <div className="sle-section-head">
            <h2>Workflow Optimization</h2>
            <Link to="/platform-builder/workflow-center" className="eds-type-small text-[var(--eds-primary)]">
              Workflow Center →
            </Link>
          </div>
          <ul className="sle-list">
            {learning.workflowOpts.map((w) => (
              <li key={w.id}>
                <div className="sle-list-top">
                  <strong>{w.title}</strong>
                  <Badge>{w.kind}</Badge>
                </div>
                <p className="eds-type-small text-[var(--eds-muted)]">{w.detail}</p>
                <p className="eds-type-small">{w.suggestion}</p>
                {w.route ? (
                  <Link to={w.route} className="eds-type-small text-[var(--eds-primary)]">
                    Открыть →
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
        </Card>

        {/* SECTION 3 — AI Performance Review */}
        <Card aria-label="AI Performance Review">
          <div className="sle-section-head">
            <h2>AI Performance Review</h2>
            <Link to="/platform-builder/ai-team" className="eds-type-small text-[var(--eds-primary)]">
              AI Team →
            </Link>
          </div>
          <div className="sle-ai-grid">
            {learning.aiReview.map((a) => (
              <div key={a.id} className="sle-ai-card">
                <strong>{a.name}</strong>
                <span className="eds-type-small">
                  {a.tasksDone} задач · {a.successPct}% · avg {a.avgSec}s
                </span>
                <Badge tone={a.knowledgeUse === "high" ? "success" : a.knowledgeUse === "medium" ? "default" : "warning"}>
                  Knowledge {a.knowledgeUse}
                </Badge>
                <p className="eds-type-small text-[var(--eds-muted)]">{a.improvement}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 4 — Knowledge Evolution */}
        <Card aria-label="Knowledge Evolution">
          <div className="sle-section-head">
            <h2>Knowledge Evolution</h2>
            <Link to="/platform-builder/knowledge" className="eds-type-small text-[var(--eds-primary)]">
              Knowledge →
            </Link>
          </div>
          <div className="sle-kb-cols">
            <div className="sle-kb-col">
              <strong className="eds-type-small">Наиболее используемые</strong>
              <ul className="eds-type-small">
                {learning.knowledge.topUsed.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div className="sle-kb-col">
              <strong className="eds-type-small">Устаревшие</strong>
              <ul className="eds-type-small">
                {learning.knowledge.stale.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div className="sle-kb-col">
              <strong className="eds-type-small">Пробелы</strong>
              <ul className="eds-type-small">
                {(learning.knowledge.gaps.length ? learning.knowledge.gaps : ["Нет критичных gaps"]).map(
                  (x) => (
                    <li key={x}>{x}</li>
                  ),
                )}
              </ul>
            </div>
            <div className="sle-kb-col">
              <strong className="eds-type-small">Обновления</strong>
              <ul className="eds-type-small">
                {learning.knowledge.updates.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>

        {/* SECTION 5 — Recommendation Center */}
        <Card aria-label="Recommendation Center">
          <div className="sle-section-head">
            <h2>Recommendation Center</h2>
            <div className="flex flex-wrap gap-1">
              {CAT_FILTER.map((c) => (
                <button
                  key={c}
                  type="button"
                  className="eds-type-small"
                  onClick={() => {
                    setCat(c);
                    void telemetry.userActivity(`sle_filter:${c}`);
                  }}
                >
                  <Badge tone={cat === c ? "success" : "default"}>
                    {c === "all" ? "All" : CAT_LABEL[c]}
                  </Badge>
                </button>
              ))}
            </div>
          </div>
          <div className="sle-reco-grid">
            {recs.map((r) => (
              <div key={r.id} className="sle-reco">
                <div className="sle-list-top">
                  <strong>{r.title}</strong>
                  <Badge>{CAT_LABEL[r.category]}</Badge>
                </div>
                <p className="eds-type-small text-[var(--eds-muted)]">{r.detail}</p>
                <Badge tone="success">{r.impact}</Badge>
                {r.route ? (
                  <Link to={r.route} className="eds-type-small text-[var(--eds-primary)]">
                    Применить →
                  </Link>
                ) : null}
              </div>
            ))}
          </div>
        </Card>

        {/* SECTION 6 — Executive Learning Report */}
        <Card aria-label="Executive Learning Report">
          <div className="sle-section-head">
            <h2>Executive Learning Report</h2>
            <span className="eds-type-small text-[var(--eds-muted)]">для руководителя</span>
          </div>
          <div className="sle-exec">
            <div className="sle-exec-block">
              <strong className="eds-type-small">Чему научилась система</strong>
              <ul className="eds-type-small">
                {learning.executive.learned.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div className="sle-exec-block">
              <strong className="eds-type-small">Что стало быстрее</strong>
              <ul className="eds-type-small">
                {learning.executive.faster.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div className="sle-exec-block">
              <strong className="eds-type-small">Что эффективнее</strong>
              <ul className="eds-type-small">
                {learning.executive.moreEffective.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div className="sle-exec-block">
              <strong className="eds-type-small">Рекомендуемые улучшения</strong>
              <ul className="eds-type-small">
                {learning.executive.recommended.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}

export function LearningStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const learning = useMemo(() => deriveLearning(snapshot, notifications), [snapshot, notifications]);
  const top = learning.recommendations[0];
  return (
    <div className="sle-strip" aria-label="Learning">
      <span className="sle-strip-label">Learning</span>
      <Badge tone="success">{learning.recommendations.length} recs</Badge>
      <Badge>~{learning.timeSavedMin} мин</Badge>
      {top ? <Badge>{CAT_LABEL[top.category]}</Badge> : null}
      <Link
        to="/platform-builder/learning"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("sle_open")}
      >
        Optimize →
      </Link>
    </div>
  );
}

/** Compact Mission Control / Control Tower widget. */
export function LearningWidgetCompact() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const learning = useMemo(() => deriveLearning(snapshot, notifications), [snapshot, notifications]);
  const top = learning.recommendations.slice(0, 2);

  return (
    <Card title="Learning Widget" className="sle-mc-compact" aria-label="Learning Widget">
      <ul className="eds-type-small">
        {top.map((r) => (
          <li key={r.id}>
            {r.title} · {r.impact}
          </li>
        ))}
      </ul>
      <div className="sle-mc-row">
        <Badge tone="success">{learning.recommendations.length} new</Badge>
        <Badge>~{learning.timeSavedMin} мин экономии</Badge>
        <Badge>{learning.metrics.find((m) => m.id === "reco_q")?.value ?? "—"}% quality</Badge>
      </div>
      <p className="eds-type-small text-[var(--eds-muted)] mb-2">
        Ожидаемый эффект: ускорение Workflow и рост качества рекомендаций AI Team.
      </p>
      <Link to="/platform-builder/learning" className="eds-type-small text-[var(--eds-primary)]">
        Self-Learning →
      </Link>
    </Card>
  );
}
