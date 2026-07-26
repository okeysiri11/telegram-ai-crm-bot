/**
 * Live Enterprise UI panels — Sprint 32.3.4.
 * Presentational only; data from useLiveEnterprise.
 */

import { Badge, Card } from "@/ui";
import type {
  AiOpsSnapshot,
  HealthStatus,
  LiveEnterpriseSnapshot,
  RecommendationItem,
  TimelineBucket,
} from "./fetchLiveEnterprise";
import type { LiveActivityItem } from "./liveEnterpriseCatalog";

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
      </Card>
    );
  }
  return (
    <Card title="Enterprise Activity Feed">
      <ul className="lo-feed">
        {items.slice(0, 10).map((a) => (
          <li key={a.id} className="lo-feed-item">
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{a.kind}</Badge>
              <span className="font-medium">{a.title}</span>
              <span className="eds-type-small text-[var(--eds-text-muted)]">{relTime(a.at)}</span>
            </div>
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              {a.detail} · {a.source}
            </p>
          </li>
        ))}
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
          <div key={h.id} className={`lo-health ${h.ok ? "is-ok" : "is-warn"}`}>
            <p className="font-medium">{h.label}</p>
            <Badge tone={h.ok ? "success" : "warning"}>{h.detail}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function AiRecommendationsPanel({ items }: { items: RecommendationItem[] }) {
  const toneLabel: Record<RecommendationItem["tone"], string> = {
    suggest: "AI рекомендует",
    today: "Сегодня желательно",
    risk: "Обнаружены риски",
    improve: "Найдено улучшение",
  };
  return (
    <Card title="AI Recommendations">
      <ul className="space-y-2">
        {items.map((r) => (
          <li key={r.id} className="lo-rec">
            <Badge>{toneLabel[r.tone]}</Badge>
            <span className="eds-type-small">{r.title}</span>
          </li>
        ))}
      </ul>
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
        обновлено {snapshot.updatedAt === new Date(0).toISOString() ? "—" : relTime(snapshot.updatedAt)} назад
      </span>
      {error ? <span className="eds-type-small text-[var(--eds-danger)]">{error}</span> : null}
      <button type="button" className="eds-type-small underline" onClick={onRefresh} disabled={busy}>
        Refresh now
      </button>
    </div>
  );
}
