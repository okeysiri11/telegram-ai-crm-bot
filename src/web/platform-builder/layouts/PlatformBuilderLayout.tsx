import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge } from "@/ui";
import { buildersForMenu } from "../managers/builderRegistry";
import { useIsPlatformOwner } from "../managers/platformOwner";
import { PLATFORM_BUILDER_SPRINT, PLATFORM_BUILDER_VERSION } from "../types";

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
      <div className="space-y-6 eds-anim-fade">
        <header className="space-y-2">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Sprint {PLATFORM_BUILDER_SPRINT} · Platform Builder · v{PLATFORM_BUILDER_VERSION}
          </p>
          <h1 className="eds-type-h1">{title}</h1>
          {subtitle ? (
            <p className="eds-type-body text-[var(--eds-text-muted)]">{subtitle}</p>
          ) : null}
        </header>

        <nav className="flex flex-wrap gap-2">
          {menu.map((item) => (
            <Link
              key={item.id}
              to={item.route}
              className="rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] px-3 py-1.5 text-xs text-[var(--eds-text)] transition hover:border-[var(--eds-primary)] eds-anim-fade"
            >
              <span className="inline-flex items-center gap-2">
                {item.name}
                {item.status === "frame" ? (
                  <>
                    <Badge>Preview</Badge>
                    <Badge tone="warning">Coming soon</Badge>
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
