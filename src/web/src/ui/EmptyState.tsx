import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Button, Card } from "@/ui";

/** Shared empty state — uses EDS Card/Button (no parallel empty-state system). */
export function EmptyState({
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
    <Card title={title}>
      {description ? <p className="eds-type-small text-[var(--eds-text-muted)]">{description}</p> : null}
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

/** Shared error page fragment for route-level failures. */
export function ErrorPage({
  title = "Something went wrong",
  message,
  children,
}: {
  title?: string;
  message?: string;
  children?: ReactNode;
}) {
  return (
    <div className="p-8">
      <h1 className="text-xl font-semibold">{title}</h1>
      {message ? (
        <pre className="mt-3 overflow-auto rounded bg-black/5 p-3 text-sm">{message}</pre>
      ) : null}
      {children}
      <div className="mt-4">
        <Link to="/workspace">
          <Button size="sm" variant="secondary">
            Back to workspace
          </Button>
        </Link>
      </div>
    </div>
  );
}
