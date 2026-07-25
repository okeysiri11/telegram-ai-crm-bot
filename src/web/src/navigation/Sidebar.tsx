import { NavLink } from "react-router-dom";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { cn } from "@/utils/cn";

const links = [
  { to: "/", key: "nav.dashboard" },
  { to: "/settings", key: "nav.settings" },
];

export function Sidebar() {
  const t = useI18n((s) => s.t);
  const modules = useWorkspaceStore((s) => s.workspace.activeModules);
  return (
    <aside className="hidden w-60 shrink-0 border-r border-[var(--ew-border)] bg-[var(--ew-surface)] p-4 md:block">
      <div className="mb-6 text-lg font-semibold tracking-tight">{t("app.title")}</div>
      <nav className="space-y-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              cn(
                "block rounded-md px-3 py-2 text-sm",
                isActive ? "bg-[var(--ew-brand-soft)] font-semibold text-[var(--ew-brand)]" : "text-[var(--ew-muted)]",
              )
            }
          >
            {t(l.key)}
          </NavLink>
        ))}
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
