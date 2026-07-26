import { NavLink } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useAuthStore } from "@/auth/authStore";
import { cn } from "@/utils/cn";
import { navigationManager } from "../../navigation/managers/navigationManager";
import { Badge } from "@/ui";
import { useIsPlatformOwner } from "../../platform-builder/managers/platformOwner";
import { moduleRegistry } from "../../workspace/managers/moduleRegistry";

export function Sidebar({
  mobileOpen = false,
  onNavigate,
}: {
  mobileOpen?: boolean;
  onNavigate?: () => void;
} = {}) {
  const t = useI18n((s) => s.t);
  const modules = useWorkspaceStore((s) => s.workspace.activeModules);
  const permissions = useWorkspaceStore((s) => s.workspace.permissions);
  const tenantId = useAuthStore((s) => s.user?.tenantId) || "demo";
  const roleId = useAuthStore((s) => s.user?.roleId);
  const isOwner = useIsPlatformOwner();

  const effectivePermissions = [
    ...permissions,
    ...(roleId ? [roleId] : []),
    ...(isOwner ? ["platform_owner", "admin"] : []),
  ];
  const items = navigationManager.forTenant(tenantId, effectivePermissions, "sidebar");
  const ecosystemLinks = moduleRegistry.ecosystems();

  const asideClass = cn(
    "w-60 shrink-0 border-r border-[var(--ew-border)] bg-[var(--ew-surface)] p-4",
    "md:block",
    mobileOpen
      ? "fixed inset-y-0 left-0 z-40 block shadow-lg"
      : "hidden",
  );

  return (
    <>
      {mobileOpen ? (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={onNavigate}
        />
      ) : null}
      <aside className={asideClass}>
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
                  onClick={onNavigate}
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
                          onClick={onNavigate}
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
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ew-muted)]">
            Workspace modules
          </div>
          <ul className="space-y-1 text-sm text-[var(--ew-muted)]">
            {modules.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </div>
        <div className="mt-6">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--ew-muted)]">
            Ecosystems
          </div>
          <ul className="space-y-1 text-sm">
            {ecosystemLinks.map((id) => (
              <li key={id}>
                <NavLink
                  to={moduleRegistry.routeFor(id)}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      "block rounded-md px-2 py-1 text-xs",
                      isActive ? "text-[var(--ew-brand)] font-medium" : "text-[var(--ew-muted)]",
                    )
                  }
                >
                  {moduleRegistry.resolve(id).title}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </>
  );
}
