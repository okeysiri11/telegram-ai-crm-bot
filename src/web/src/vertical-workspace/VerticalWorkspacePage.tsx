/**
 * Sprint 42.8 — оболочка вертикали: боковая навигация + контент.
 */

import { Link, useParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { cn } from "@/utils/cn";
import { getVertical, sectionPath } from "./catalog";
import { useVerticalWorkspaceStore } from "./verticalWorkspaceStore";
import { VerticalDashboard } from "./VerticalDashboard";
import { useEffect } from "react";

export function VerticalWorkspacePage() {
  const { verticalId = "owner", sectionId } = useParams<{
    verticalId: string;
    sectionId?: string;
  }>();
  const setVerticalId = useVerticalWorkspaceStore((s) => s.setVerticalId);
  const vertical = getVertical(verticalId);

  useEffect(() => {
    if (vertical) setVerticalId(vertical.id);
  }, [vertical, setVerticalId]);

  if (!vertical) {
    return (
      <WorkspaceLayout>
        <div className="p-6" data-testid="vertical-not-found">
          <h1 className="eds-type-title">Рабочее пространство не найдено</h1>
          <p className="mt-2 eds-type-body text-[var(--eds-text-muted)]">
            Выберите пространство в переключателе верхней панели.
          </p>
          <Link to="/vertical/owner" className="mt-4 inline-block text-[var(--eds-accent)]">
            Открыть Owner
          </Link>
        </div>
      </WorkspaceLayout>
    );
  }

  const activeSection = sectionId || "home";

  return (
    <WorkspaceLayout>
      <div className="uvw-shell" data-testid="vertical-workspace-shell" data-vertical={vertical.id}>
        <aside className="uvw-side" aria-label={`Навигация · ${vertical.label}`}>
          <div className="uvw-side-head">
            <p className="eds-type-caption text-[var(--eds-text-muted)]">Рабочее пространство</p>
            <h2 className="eds-type-section">{vertical.label}</h2>
            <p className="eds-type-helper mt-1">{vertical.purpose}</p>
          </div>
          <nav className="uvw-side-nav">
            {vertical.nav.map((item) => {
              const to = item.href || sectionPath(vertical.id, item.id);
              const active =
                item.id === activeSection ||
                (item.id === "home" && activeSection === "home" && !sectionId);
              return (
                <Link
                  key={item.id}
                  to={to}
                  className={cn("uvw-side-link", active && "is-active")}
                  data-nav={item.id}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          {vertical.legacyRoute ? (
            <div className="uvw-side-foot">
              <Link to={vertical.legacyRoute} className="eds-type-caption text-[var(--eds-accent)]">
                Полный модуль →
              </Link>
            </div>
          ) : null}
        </aside>
        <div className="uvw-main">
          <VerticalDashboard vertical={vertical} sectionId={activeSection} />
        </div>
      </div>
    </WorkspaceLayout>
  );
}
