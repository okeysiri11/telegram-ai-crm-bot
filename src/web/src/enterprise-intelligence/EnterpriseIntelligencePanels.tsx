/**
 * Enterprise Intelligence panels — Sprint 32.5.
 * Presentational layer; reuses shared live-ops poller.
 */

import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveIntelligence, type EnterpriseInsight, type SmartPriority } from "./deriveIntelligence";
import { dismissDailyBrief, isDailyBriefDismissed } from "./dailyBriefPref";

const INSIGHT_TONE: Record<EnterpriseInsight["category"], "default" | "success" | "warning" | "danger"> = {
  event: "default",
  anomaly: "warning",
  risk: "danger",
  achievement: "success",
  opportunity: "success",
};

const PRIORITY_LABEL: Record<SmartPriority["bucket"], string> = {
  urgent: "Срочно",
  important: "Важно",
  awaiting: "Ожидает",
  recommended: "Рекомендация",
};

export function EnterpriseIntelligenceLayer({ compact = false }: { compact?: boolean }) {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const navigate = useNavigate();
  const intel = useMemo(() => deriveIntelligence(snapshot, notifications), [snapshot, notifications]);
  const [briefOpen, setBriefOpen] = useState(() => !isDailyBriefDismissed());
  const [expanded, setExpanded] = useState(!compact);

  return (
    <div className={`ei-layer${compact ? " is-compact" : ""} eds-anim-fade`}>
      {briefOpen ? (
        <Card title="Daily Brief" className="ei-brief">
          <p className="font-semibold">{intel.brief.greeting}</p>
          <p className="mb-2 eds-type-small text-[var(--eds-text-muted)]">Сегодня:</p>
          <ul className="space-y-1 eds-type-small">
            {intel.brief.bullets.map((b) => (
              <li key={b}>· {b}</li>
            ))}
          </ul>
          {intel.knowledgeAware ? (
            <p className="mt-2">
              <Badge tone="success">Knowledge awareness</Badge>
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              size="sm"
              onClick={() => {
                void telemetry.userActivity("ei_brief_dashboard");
                navigate("/dashboard?mode=executive");
              }}
            >
              Executive Decision
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                dismissDailyBrief();
                setBriefOpen(false);
                void telemetry.userActivity("ei_brief_dismiss");
              }}
            >
              Скрыть на сегодня
            </Button>
          </div>
        </Card>
      ) : null}

      <div className="ei-toolbar">
        <span className="ei-toolbar-label">Enterprise Intelligence</span>
        {intel.knowledgeAware ? <Badge tone="success">KB</Badge> : null}
        <Button size="sm" variant="ghost" onClick={() => setExpanded((v) => !v)}>
          {expanded ? "Свернуть" : "Insights"}
        </Button>
        {!briefOpen ? (
          <Button size="sm" variant="ghost" onClick={() => setBriefOpen(true)}>
            Brief
          </Button>
        ) : null}
      </div>

      {expanded ? (
        <div className={`ei-grid${compact ? " is-compact" : ""}`}>
          <InsightsPanel insights={intel.insights} />
          <PrioritiesPanel priorities={intel.priorities} />
          <CrossModulePanel links={intel.crossModule} />
          <DecisionPanel decision={intel.decision} />
        </div>
      ) : null}
    </div>
  );
}

/** Dashboard-only fuller surface — same derive, no extra fetch when shared snapshot warm. */
export function EnterpriseIntelligenceDashboard() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const intel = useMemo(() => deriveIntelligence(snapshot, notifications), [snapshot, notifications]);

  return (
    <div className="ei-dashboard eds-anim-fade">
      <div className="cc-section-head">
        <h2>Enterprise Intelligence</h2>
        {intel.knowledgeAware ? <Badge tone="success">Knowledge awareness</Badge> : null}
      </div>
      <div className="ei-grid">
        <InsightsPanel insights={intel.insights} />
        <PrioritiesPanel priorities={intel.priorities} />
        <CrossModulePanel links={intel.crossModule} />
        <DecisionPanel decision={intel.decision} />
      </div>
      <Card title="Daily Brief" className="mt-3">
        <p className="font-semibold">{intel.brief.greeting}</p>
        <ul className="mt-2 space-y-1 eds-type-small">
          {intel.brief.bullets.map((b) => (
            <li key={b}>· {b}</li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function InsightsPanel({ insights }: { insights: EnterpriseInsight[] }) {
  const navigate = useNavigate();
  const byCat = (cat: EnterpriseInsight["category"]) => insights.filter((i) => i.category === cat);
  const blocks: Array<{ cat: EnterpriseInsight["category"]; label: string }> = [
    { cat: "event", label: "События дня" },
    { cat: "anomaly", label: "Отклонения" },
    { cat: "risk", label: "Риски" },
    { cat: "achievement", label: "Достижения" },
    { cat: "opportunity", label: "Возможности" },
  ];
  return (
    <Card title="Enterprise Insights" className="ei-card">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
        {blocks.map(({ cat, label }) => {
          const items = byCat(cat).slice(0, 2);
          return (
            <div key={cat}>
              <p className="mb-1 font-medium eds-type-small">{label}</p>
              <ul className="space-y-1 eds-type-small text-[var(--eds-text-muted)]">
                {items.length ? (
                  items.map((i) => (
                    <li key={i.id}>
                      <button
                        type="button"
                        className="ei-link"
                        onClick={() => {
                          if (i.route) {
                            void telemetry.userActivity(`ei_insight:${i.id}`);
                            navigate(i.route);
                          }
                        }}
                      >
                        <Badge tone={INSIGHT_TONE[cat]}>{cat}</Badge> {i.title}
                      </button>
                    </li>
                  ))
                ) : (
                  <li>· Нет сигналов</li>
                )}
              </ul>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function PrioritiesPanel({ priorities }: { priorities: SmartPriority[] }) {
  const navigate = useNavigate();
  const buckets: SmartPriority["bucket"][] = ["urgent", "important", "awaiting", "recommended"];
  return (
    <Card title="Smart Priorities" className="ei-card">
      <div className="space-y-3">
        {buckets.map((bucket) => {
          const items = priorities.filter((p) => p.bucket === bucket).slice(0, 3);
          return (
            <div key={bucket}>
              <p className="mb-1 font-medium eds-type-small">{PRIORITY_LABEL[bucket]}</p>
              <ul className="space-y-1 eds-type-small">
                {items.length ? (
                  items.map((p) => (
                    <li key={p.id}>
                      <button
                        type="button"
                        className="ei-link"
                        onClick={() => {
                          if (p.route) {
                            void telemetry.userActivity(`ei_priority:${p.id}`);
                            navigate(p.route);
                          }
                        }}
                      >
                        {p.title}
                        <span className="block text-[var(--eds-text-muted)]">{p.detail}</span>
                      </button>
                    </li>
                  ))
                ) : (
                  <li className="text-[var(--eds-text-muted)]">· Пусто</li>
                )}
              </ul>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function CrossModulePanel({
  links,
}: {
  links: ReturnType<typeof deriveIntelligence>["crossModule"];
}) {
  return (
    <Card title="Cross-Module Intelligence" className="ei-card">
      <ul className="space-y-2 eds-type-small">
        {links.map((l) => (
          <li key={l.id}>
            <Link
              to={l.route || "/dashboard"}
              className="ei-link"
              onClick={() => void telemetry.userActivity(`ei_cross:${l.id}`)}
            >
              <Badge>
                {l.from} → {l.to}
              </Badge>{" "}
              <span className="font-medium">{l.title}</span>
              <span className="block text-[var(--eds-text-muted)]">{l.detail}</span>
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function DecisionPanel({
  decision,
}: {
  decision: ReturnType<typeof deriveIntelligence>["decision"];
}) {
  const navigate = useNavigate();
  return (
    <Card title="Executive Decision Panel" className="ei-card ei-decision">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="mb-1 font-medium eds-type-small">Требует решения сегодня</p>
          <ul className="eds-type-small space-y-1">
            {decision.decideToday.map((p) => (
              <li key={p.id}>
                <button type="button" className="ei-link" onClick={() => p.route && navigate(p.route)}>
                  · {p.title}
                </button>
              </li>
            ))}
            {!decision.decideToday.length ? <li className="text-[var(--eds-text-muted)]">· Нет срочного</li> : null}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium eds-type-small">Может подождать</p>
          <ul className="eds-type-small space-y-1 text-[var(--eds-text-muted)]">
            {decision.canWait.map((p) => (
              <li key={p.id}>· {p.title}</li>
            ))}
            {!decision.canWait.length ? <li>· Очередь свободна</li> : null}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium eds-type-small">Риски</p>
          <ul className="eds-type-small space-y-1">
            {decision.risks.map((r) => (
              <li key={r.id}>
                <Badge tone="danger">{r.title}</Badge>
              </li>
            ))}
            {!decision.risks.length ? <li className="text-[var(--eds-text-muted)]">· Критичных нет</li> : null}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium eds-type-small">Возможности</p>
          <ul className="eds-type-small space-y-1">
            {decision.opportunities.map((o) => (
              <li key={o.id}>
                <Badge tone="success">{o.title}</Badge>
              </li>
            ))}
            {!decision.opportunities.length ? <li className="text-[var(--eds-text-muted)]">· Пока тихо</li> : null}
          </ul>
        </div>
      </div>
      <div className="mt-3">
        <Link to="/dashboard?mode=executive">
          <Button size="sm" variant="secondary">
            Открыть Executive Mode
          </Button>
        </Link>
      </div>
    </Card>
  );
}
