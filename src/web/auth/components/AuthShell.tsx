import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function AuthShell({ title, subtitle, children, footer }: { title: string; subtitle?: string; children: ReactNode; footer?: ReactNode }) {
  return (
    <div className="flex min-h-full items-center justify-center bg-[linear-gradient(160deg,var(--eds-primary)_0%,#142033_55%,var(--eds-bg)_100%)] p-4 sm:p-6">
      <div className="w-full max-w-md rounded-[var(--eds-radius-lg)] bg-[var(--eds-surface)] p-4 sm:p-6 shadow-[var(--eds-shadow-lg)] edm-overlay-panel">
        <h1 className="eds-type-h2 mb-1 text-[var(--eds-text)]">{title}</h1>
        {subtitle ? <p className="eds-type-small mb-6 text-[var(--eds-text-muted)]">{subtitle}</p> : <div className="mb-6" />}
        {children}
        {footer ? <div className="mt-4 eds-type-small text-[var(--eds-text-muted)]">{footer}</div> : null}
      </div>
    </div>
  );
}

export function AuthLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="text-[var(--eds-primary)] underline-offset-2 hover:underline">
      {children}
    </Link>
  );
}
