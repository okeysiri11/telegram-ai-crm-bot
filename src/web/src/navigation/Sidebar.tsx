import { NavLink } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { cn } from "@/utils/cn";
import { navigationManager } from "../../navigation/managers/navigationManager";
import { Badge } from "@/ui";
import { useIsPlatformOwner } from "../../platform-builder/managers/platformOwner";

export function Sidebar() {
  const t = useI18n((s) => s.t);
  const modules = useWorkspaceStore((s) => s.workspace.activeModules);
  const items = navigationManager.get("sidebar");
  const isOwner = useIsPlatformOwner();

  return (
    <aside className="hidden w-60 shrink-0 border-r border-[var(--ew-border)] bg-[var(--ew-surface)] p-4 md:block">
      <div className="mb-6 text-lg font-semibold tracking-tight">{t("app.title")}</div>
      <nav className="space-y-1">
        {items.map((item) => {
          const children = (item.children || []).filter((child) => {
            if (child.permissions.includes("platform_owner") && !isOwner) return false;
            return true;
          });
          return (
            <div key={item.id}>
              <NavLink
                to={item.route}
                end={item.route === "/workspace"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center justify-between rounded-md px-3 py-2 text-sm",
                    isActive
                      ? "bg-[var(--ew-brand-soft)] font-semibold text-[var(--ew-brand)]"
                      : "text-[var(--ew-muted)]",
                  )
                }
              >
                <span>{item.name}</span>
                {item.badge ? <Badge>{item.badge}</Badge> : null}
              </NavLink>
              {children.length ? (
                <ul className="ml-3 space-y-1 border-l border-[var(--ew-border)] pl-2">
                  {children.map((child) => (
                    <li key={child.id}>
                      <NavLink
                        to={child.route}
                        className={({ isActive }) =>
                          cn(
                            "block rounded-md px-2 py-1 text-xs",
                            isActive ? "text-[var(--ew-brand)] font-medium" : "text-[var(--ew-muted)]",
                          )
                        }
                      >
                        {child.name}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          );
        })}
      </nav>
      <div className="mt-8">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ew-muted)]">Modules</div>
        <ul className="space-y-1 text-sm text-[var(--ew-muted)]">
          {modules.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
