import type { ReactNode } from "react";
import { Button } from "@/ui";

/** Lightweight loading overlay for workspace transitions. */
export function LoadingOverlay({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="ews-loading-overlay" role="status" aria-live="polite">
      <div className="ews-loading-card ews-glass">
        <div className="ews-progress" aria-hidden>
          <span />
        </div>
        <p className="eds-type-small mt-2">{label}</p>
      </div>
    </div>
  );
}

export function WorkspaceErrorState({
  title = "Something went wrong",
  detail,
  onRetry,
}: {
  title?: string;
  detail?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="ews-error-state ews-glass" role="alert">
      <h2 className="eds-type-title">{title}</h2>
      {detail ? <p className="mt-2 eds-type-body text-[var(--eds-text-muted)]">{detail}</p> : null}
      {onRetry ? (
        <div className="mt-3">
          <Button size="sm" onClick={onRetry}>
            Retry
          </Button>
        </div>
      ) : null}
    </div>
  );
}

export function ModuleSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="ews-module-section">
      <h2 className="eds-type-section mb-2">{title}</h2>
      {children}
    </section>
  );
}
