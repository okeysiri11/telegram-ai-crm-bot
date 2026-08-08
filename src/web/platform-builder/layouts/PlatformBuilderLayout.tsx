import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge } from "@/ui";
import { buildersForMenu } from "../managers/builderRegistry";
import { useIsPlatformOwner } from "../managers/platformOwner";
import { PLATFORM_BUILDER_SPRINT, PLATFORM_BUILDER_VERSION } from "../types";
import { builderDisplayName, term } from "@/i18n/platformGlossary";

/**
 * Hotfix 42.4.1 — все пункты меню берутся из BUILDER_NAV_RU (единый словарь).
 */
export function PlatformBuilderLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  const owner = useIsPlatformOwner();
  const menu = buildersForMenu(owner);

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade pb-layout" data-testid="platform-builder-layout-ru">
        <header className="space-y-2">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Спринт {PLATFORM_BUILDER_SPRINT} · Конструктор платформы · v{PLATFORM_BUILDER_VERSION}
          </p>
          <h1 className="eds-type-h1">{title}</h1>
          {subtitle ? (
            <p className="eds-type-body text-[var(--eds-text-muted)]">{subtitle}</p>
          ) : null}
        </header>

        <nav className="flex flex-wrap gap-2" aria-label="Навигация конструктора" data-testid="builder-nav-ru">
          {menu.map((item) => (
            <Link
              key={item.id}
              to={item.route}
              className="rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] px-3 py-1.5 text-xs text-[var(--eds-text)] transition hover:border-[var(--eds-primary)] eds-anim-fade"
              data-builder-id={item.id}
            >
              <span className="inline-flex items-center gap-2">
                {builderDisplayName(item.id, item.name)}
                {item.status === "frame" ? (
                  <>
                    <Badge>{term("preview")}</Badge>
                    <Badge tone="warning">{term("comingSoon")}</Badge>
                  </>
                ) : null}
              </span>
            </Link>
          ))}
        </nav>

        {children}
      </div>
    </WorkspaceLayout>
  );
}
