import type { ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { cn } from "@/utils/cn";
import { RECRUITING_NAV } from "./recruitingLabels";

type Props = {
  title: string;
  subtitle: string;
  children: ReactNode;
  testId?: string;
  error?: string | null;
  onRefresh?: () => void;
  headerExtra?: ReactNode;
};

export function RecruitingOpsFrame({ title, subtitle, children, testId, error, onRefresh, headerExtra }: Props) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <WorkspaceLayout>
      <div className="biz-cabinet grid gap-4 lg:grid-cols-[14rem_minmax(0,1fr)]" data-testid={testId}>
        <aside className="rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface)] p-3 hidden lg:block" data-testid="ops-side-nav">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">Рабочее пространство</p>
          <h1 className="eds-type-section mt-1">Рекрутинг</h1>
          <p className="eds-type-helper mt-1 text-[var(--eds-text-muted)]">CRM найма. Vanguard — один из проектов.</p>
          <nav className="mt-3 flex flex-col gap-1" aria-label="Разделы">
            {RECRUITING_NAV.map((item) => {
              const active =
                item.id === "projects"
                  ? location.pathname.startsWith("/workspace/recruiting/projects")
                  : location.pathname + location.search === item.href ||
                    (item.id === "home" && location.pathname === "/workspace/recruiting" && !location.search.includes("view="));
              return (
                <button
                  key={item.id}
                  type="button"
                  className={cn(
                    "rounded-md px-2 py-1.5 text-left eds-type-small",
                    active ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]" : "hover:bg-[var(--eds-primary-soft)]/40",
                  )}
                  onClick={() => navigate(item.href)}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
          {onRefresh ? (
            <Button size="sm" variant="secondary" className="mt-4" onClick={onRefresh}>
              Обновить
            </Button>
          ) : null}
        </aside>
        <main className="min-w-0">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="eds-type-section">{title}</h2>
              <p className="eds-type-helper text-[var(--eds-text-muted)]">{subtitle}</p>
            </div>
            {headerExtra}
          </div>
          {error ? (
            <p className="mb-3 eds-type-body text-[var(--eds-danger,#b91c1c)]" data-testid="ops-error-state">
              {error}
            </p>
          ) : null}
          {children}
        </main>
      </div>
    </WorkspaceLayout>
  );
}

export function displayMetric(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Нет данных";
  return String(value);
}
