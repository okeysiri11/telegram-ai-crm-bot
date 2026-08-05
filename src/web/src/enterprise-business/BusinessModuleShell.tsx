/**
 * Sprint 30.8 — Shared Russian business-module chrome (tabs + permissions).
 */

import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button } from "@/ui";
import { PermissionGuard } from "@/shell/PermissionGuard";

export type BusinessTab = { id: string; label: string };

type Props = {
  title: string;
  subtitle: string;
  tabs: BusinessTab[];
  activeTab: string;
  onTab: (id: string) => void;
  source?: string;
  permissions?: string[];
  actions?: ReactNode;
  children: ReactNode;
  testId?: string;
};

export function BusinessModuleShell({
  title,
  subtitle,
  tabs,
  activeTab,
  onTab,
  source,
  permissions = ["read"],
  actions,
  children,
  testId,
}: Props) {
  return (
    <PermissionGuard require={permissions}>
      <WorkspaceLayout>
        <div className="space-y-4" data-testid={testId}>
          <header className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="mb-2 flex flex-wrap gap-2">
                <Badge tone="success">Sprint 30.8</Badge>
                {source ? <Badge>{source}</Badge> : null}
              </div>
              <h1 className="eds-type-h1">{title}</h1>
              <p className="eds-type-helper">{subtitle}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {actions}
              <Link to="/search">
                <Button size="sm" variant="ghost">
                  Поиск
                </Button>
              </Link>
            </div>
          </header>

          <nav className="flex flex-wrap gap-1 border-b border-[var(--eds-border)] pb-2" aria-label="Разделы модуля">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`rounded-md px-3 py-1.5 eds-type-small ${
                  activeTab === t.id
                    ? "bg-[var(--eds-primary)] text-white"
                    : "hover:bg-[var(--eds-surface-muted)]"
                }`}
                onClick={() => onTab(t.id)}
                aria-current={activeTab === t.id ? "page" : undefined}
              >
                {t.label}
              </button>
            ))}
          </nav>

          {children}
        </div>
      </WorkspaceLayout>
    </PermissionGuard>
  );
}
