import { NavLink } from "react-router-dom";
import { cn } from "../../utils/cn";

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/workflows", label: "Workflows" },
  { to: "/agents", label: "AI Agents" },
  { to: "/providers", label: "Providers" },
  { to: "/chat-bridge", label: "ChatGPT Bridge" },
  { to: "/voice", label: "Voice Center" },
  { to: "/mcp", label: "MCP Gateway" },
  { to: "/execution", label: "Execution Planner" },
  { to: "/memory", label: "Memory" },
  { to: "/timeline", label: "Timeline" },
  { to: "/tasks", label: "Tasks" },
  { to: "/queue", label: "Queue" },
  { to: "/metrics", label: "Metrics" },
  { to: "/kernel", label: "Kernel" },
  { to: "/services", label: "Services" },
  { to: "/knowledge", label: "Knowledge" },
  { to: "/logs", label: "Logs" },
  { to: "/events", label: "Events" },
  { to: "/marketplace", label: "Marketplace" },
  { to: "/settings", label: "Settings" },
];

export function Sidebar({ collapsed }: { collapsed: boolean }) {
  return (
    <aside
      className={cn(
        "glass flex h-full flex-col border-r transition-all",
        collapsed ? "w-16" : "w-60",
      )}
    >
      <div className="flex h-14 items-center border-b border-[var(--border)] px-4">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-500" />
          {!collapsed && (
            <div>
              <div className="text-sm font-semibold">ADOS Control</div>
              <div className="text-[10px] uppercase tracking-widest text-[var(--muted)]">
                Enterprise OS
              </div>
            </div>
          )}
        </div>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-2">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "block rounded-xl px-3 py-2 text-sm transition",
                isActive
                  ? "bg-sky-500/20 text-sky-200"
                  : "text-[var(--muted)] hover:bg-white/5 hover:text-white",
              )
            }
          >
            {collapsed ? item.label.slice(0, 1) : item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
