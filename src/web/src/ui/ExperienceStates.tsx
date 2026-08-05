/**
 * Unified experience surfaces — Sprint 32.3.5 / EP-03 motion.
 * Skeleton / Empty / Success reuse EDS + MDL tokens — no parallel design system.
 */

import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Button, Card } from "@/ui";

export function Skeleton({
  className = "",
  rows = 3,
  height = "1rem",
}: {
  className?: string;
  rows?: number;
  height?: string;
}) {
  return (
    <div className={`eds-skeleton-stack ${className}`} aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="edm-skeleton"
          style={{ height, width: i === rows - 1 ? "70%" : "100%" }}
        />
      ))}
    </div>
  );
}

export function SuccessState({
  title,
  description,
  actionLabel,
  actionTo,
}: {
  title: string;
  description?: string;
  actionLabel?: string;
  actionTo?: string;
}) {
  return (
    <Card title={title} success className="eds-state eds-state-success edm-ai-done">
      <p className="eds-type-small text-[var(--eds-text-muted)]">{description || "Операция выполнена успешно."}</p>
      {actionLabel && actionTo ? (
        <div className="mt-3">
          <Link to={actionTo}>
            <Button size="sm">{actionLabel}</Button>
          </Link>
        </div>
      ) : null}
    </Card>
  );
}

/** Compact loading block for widgets (not full-page LoadingScreen). */
export function WidgetLoading({ label = "Загрузка…" }: { label?: string }) {
  return (
    <div className="eds-widget-loading eds-anim-fade">
      <span className="eds-anim-loading" aria-hidden />
      <span className="eds-type-small text-[var(--eds-text-muted)]">{label}</span>
      <span className="edm-stream-bar w-full max-w-[12rem]" aria-hidden />
    </div>
  );
}

/** Soft refresh overlay for partial / background updates. */
export function Refreshing({ children, active }: { children: ReactNode; active: boolean }) {
  return <div className={active ? "edm-refreshing" : undefined}>{children}</div>;
}

export function ExperienceState({
  kind,
  title,
  description,
  actionLabel,
  actionTo,
  children,
}: {
  kind: "empty" | "loading" | "error" | "success" | "refreshing" | "streaming";
  title: string;
  description?: string;
  actionLabel?: string;
  actionTo?: string;
  children?: ReactNode;
}) {
  if (kind === "loading" || kind === "refreshing") {
    return (
      <Card title={title} loading={kind === "refreshing"} className="eds-state eds-anim-fade">
        {kind === "refreshing" ? <div className="edm-stream-bar mb-3" aria-hidden /> : null}
        <Skeleton rows={4} />
        {description ? <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">{description}</p> : null}
      </Card>
    );
  }
  if (kind === "streaming") {
    return (
      <Card title={title} className="eds-state edm-ai-analyzing">
        <p className="eds-type-helper">{description || "Обновление данных…"}</p>
        {children}
      </Card>
    );
  }
  if (kind === "success") {
    return <SuccessState title={title} description={description} actionLabel={actionLabel} actionTo={actionTo} />;
  }
  if (kind === "error") {
    return (
      <Card title={title} className="eds-state eds-state-error eds-anim-fade">
        <p className="eds-type-small text-[var(--eds-danger)]">{description || "Не удалось загрузить данные."}</p>
        {actionLabel && actionTo ? (
          <div className="mt-3">
            <Link to={actionTo}>
              <Button size="sm" variant="secondary">
                {actionLabel}
              </Button>
            </Link>
          </div>
        ) : null}
        {children}
      </Card>
    );
  }
  return (
    <Card title={title} empty className="eds-state eds-state-empty eds-anim-scale">
      <div className="eds-empty-art" aria-hidden>
        ◇
      </div>
      <p className="eds-type-small text-[var(--eds-text-muted)]">
        {description || "Пока здесь пусто — начните с первого действия."}
      </p>
      {actionLabel && actionTo ? (
        <div className="mt-3">
          <Link to={actionTo}>
            <Button size="sm">{actionLabel}</Button>
          </Link>
        </div>
      ) : null}
      {children}
    </Card>
  );
}
