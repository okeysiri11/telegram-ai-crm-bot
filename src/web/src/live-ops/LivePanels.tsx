/**
 * Live Enterprise UI panels — Sprint 32.3.4.
 * Presentational only; data from useLiveEnterprise.
 * Sprint 33.8 — Concierge recommendations show goal alignment via OKR derive.
 */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import type {
  AiOpsSnapshot,
  HealthStatus,
  LiveEnterpriseSnapshot,
  RecommendationItem,
  TimelineBucket,
} from "./fetchLiveEnterprise";
import type { LiveActivityItem } from "./liveEnterpriseCatalog";
import { useLiveEnterprise } from "./useLiveEnterprise";
import { useNotificationStore } from "@/notifications/notificationStore";
import { alignRecommendation, deriveOkr } from "@/enterprise-okr/deriveOkr";

function relTime(iso: string) {
  const diff = Date.now() - Date.parse(iso);
  if (Number.isNaN(diff)) return "";
  const m = Math.max(0, Math.round(diff / 60_000));
  if (m < 1) return "сейчас";
  if (m < 60) return `${m}м`;
  const h = Math.round(m / 60);
  return `${h}ч`;
}

export function ActivityFeedPanel({ items }: { items: LiveActivityItem[] }) {
  if (!items.length) {
    return (
      <Card title="Enterprise Activity Feed" className="eds-anim-fade">
        <div className="eds-empty-art" aria-hidden>
          ◇
        </div>
        <p className="eds-type-small text-[var(--eds-text-muted)]">Пока нет событий — система ожидает активность.</p>
        <div className="mt-3">
          <Link to="/platform-builder/mission-control" className="eds-type-small text-[var(--eds-primary)]">
            Mission Control →
          </Link>
        </div>
      </Card>
    );
  }
  return (
    <Card title="Enterprise Activity Feed">
      <ul className="lo-feed">
        {items.slice(0, 8).map((a) => {
          const route =
            a.kind === "ai"
              ? "/platform-builder/ai-team"
              : a.source === "mission_control"
                ? "/platform-builder/mission-control"
                : "/platform-builder/control-tower";
          return (
            <li key={a.id} className="lo-feed-item">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{a.kind}</Badge>
                <span className="font-medium">{a.title}</span>
                <span className="eds-type-small text-[var(--eds-text-muted)]">{relTime(a.at)}</span>
              </div>
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Что: {a.title}
              </p>
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Почему: {a.detail || a.source}
              </p>
              <Link to={route} className="eds-type-small text-[var(--eds-primary)]">
                Act on this signal →
              </Link>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

export function AiOperationsPanel({ ops }: { ops: AiOpsSnapshot }) {
  return (
    <Card title="AI Operations">
      <div className="mb-3 flex flex-wrap gap-2">
        <Badge tone={ops.status === "operational" || ops.status === "ok" ? "success" : "warning"}>
          {ops.status}
        </Badge>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <div>
          <p className="mb-1 font-medium">Работающие AI</p>
          <ul className="space-y-1 eds-type-small">
            {ops.running.map((x) => (
              <li key={x}>
                <Badge tone="success">{x}</Badge>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium">Очередь</p>
          <ul className="space-y-1 eds-type-small text-[var(--eds-text-muted)]">
            {ops.queue.map((x) => (
              <li key={x}>· {x}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium">Последние действия</p>
          <ul className="space-y-1 eds-type-small text-[var(--eds-text-muted)]">
            {ops.recent.map((x) => (
              <li key={x}>· {x}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium">Завершённые</p>
          <ul className="space-y-1 eds-type-small">
            {ops.completed.map((x) => (
              <li key={x}>· {x}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium">Ошибки</p>
          {ops.errors.length ? (
            <ul className="space-y-1 eds-type-small text-[var(--eds-danger)]">
              {ops.errors.map((x) => (
                <li key={x}>· {x}</li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">Нет ошибок</p>
          )}
        </div>
      </div>
    </Card>
  );
}

export function MissionTimelinePanel({ buckets }: { buckets: TimelineBucket[] }) {
  return (
    <Card title="Mission Timeline">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {buckets.map((b) => (
          <div key={b.id} className="lo-timeline-bucket">
            <p className="mb-2 eds-type-caption uppercase tracking-[0.12em] text-[var(--eds-text-muted)]">
              {b.label}
            </p>
            <ul className="space-y-1 eds-type-small">
              {b.items.map((x) => (
                <li key={`${b.id}_${x}`}>· {x}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function EnterpriseHealthPanel({ health }: { health: HealthStatus[] }) {
  return (
    <Card title="Enterprise Health">
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {health.map((h) => (
          <Link
            key={h.id}
            to={h.ok ? "/platform-builder/mission-control" : "/platform-builder/control-tower"}
            className={`lo-health ${h.ok ? "is-ok" : "is-warn"}`}
          >
            <p className="font-medium">{h.label}</p>
            <Badge tone={h.ok ? "success" : "warning"}>{h.detail}</Badge>
            <p className="eds-type-small text-[var(--eds-text-muted)] mt-1">
              {h.ok ? "Стабильно — наблюдать" : "Важно — разобрать сейчас"}
            </p>
            <span className="eds-type-small text-[var(--eds-primary)]">{h.ok ? "MC →" : "Tower →"}</span>
          </Link>
        ))}
      </div>
    </Card>
  );
}

export function AiRecommendationsPanel({ items }: { items: RecommendationItem[] }) {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const goals = useMemo(() => deriveOkr(snapshot, notifications).goals, [snapshot, notifications]);
  const toneLabel: Record<RecommendationItem["tone"], string> = {
    suggest: "Insight",
    today: "Today",
    risk: "Risk",
    improve: "Improve",
  };
  return (
    <Card title="Executive Advisor · Recommendations">
      <p className="mb-2 eds-type-helper">Observation · Why · Action · Impact</p>
      <ul className="space-y-2">
        {items.map((r) => {
          const align = alignRecommendation(r, goals);
          const route =
            r.tone === "risk"
              ? "/platform-builder/control-tower"
              : /crm|сделк/i.test(r.title)
                ? "/workspace/crm"
                : "/platform-builder/concierge";
          const confidence = r.tone === "risk" || r.tone === "today" ? "High" : r.tone === "improve" ? "Likely" : "Likely";
          return (
            <li key={r.id} className="lo-rec ai-advisor-rec">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{toneLabel[r.tone]}</Badge>
                <Badge tone="success">{align.goalLabel}</Badge>
                <Badge tone={confidence === "High" ? "success" : "default"}>{confidence}</Badge>
              </div>
              <span className="eds-type-small font-medium">Observation: {r.title}</span>
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Why: {align.expectedEffect}
              </p>
              <p className="eds-type-small text-[var(--eds-text-muted)]">Impact: KPI {align.kpi}</p>
              <Link to={route} className="eds-type-small text-[var(--eds-primary)]">
                Take suggested action →
              </Link>
            </li>
          );
        })}
      </ul>
      <Link to="/platform-builder/okr" className="eds-type-small text-[var(--eds-primary)] mt-2 inline-block">
        OKR alignment →
      </Link>
    </Card>
  );
}

export function LiveMetaBar({
  snapshot,
  busy,
  error,
  onRefresh,
}: {
  snapshot: LiveEnterpriseSnapshot;
  busy: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <div className="lo-meta">
      <Badge tone={snapshot.mcOk ? "success" : "warning"}>Live · {busy ? "updating…" : "ready"}</Badge>
      <span className="eds-type-small text-[var(--eds-text-muted)]">
        updated {snapshot.updatedAt === new Date(0).toISOString() ? "—" : relTime(snapshot.updatedAt)} ago
      </span>
      {error ? (
        <span className="eds-type-small text-[var(--eds-danger)]" role="status">
          Live refresh paused — last snapshot kept. {error}
        </span>
      ) : null}
      <button type="button" className="eds-type-small underline" onClick={onRefresh} disabled={busy}>
        {busy ? "Refreshing…" : "Refresh now"}
      </button>
    </div>
  );
}
