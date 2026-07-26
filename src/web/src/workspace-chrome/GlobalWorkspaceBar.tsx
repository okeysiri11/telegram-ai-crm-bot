/**
 * Global Workspace chrome — Sprint 32.3.6.
 * Context bar + Quick Switch — client-side navigate only.
 */

import { Link, useLocation, useNavigate } from "react-router-dom";
import { Badge, Button } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { useCommandCenterUi } from "../../command-center/components/CommandCenterProvider";
import { telemetry } from "@/integrations/telemetry";
import {
  GLOBAL_QUICK_SWITCH,
  detectActiveEcosystem,
  workspaceStatusLabel,
} from "./workspaceContext";

export function GlobalWorkspaceBar() {
  const loc = useLocation();
  const navigate = useNavigate();
  const { openPalette, openQuickSwitcher } = useNavigationUi();
  const { openOmnibox } = useCommandCenterUi();
  const user = useAuthStore((s) => s.user);
  const ws = useWorkspaceStore((s) => s.workspace);
  const first = loadFirstEntry();
  const role = firstEntryRoleCatalog.get(first.roleId);
  const roleLabel = role?.label || user?.roleId || user?.roles?.[0] || ws.userContext || "User";
  const company = first.companyName || ws.company;
  const ecosystem = detectActiveEcosystem(loc.pathname) || "Platform";
  const concierge = first.conciergeName || "AI Concierge";
  const status = workspaceStatusLabel(ws.activeModules);

  return (
    <div className="uws-chrome eds-anim-fade">
      <div className="uws-context" aria-label="Workspace context">
        <Badge>{company}</Badge>
        <Badge>{ws.project || "workspace"}</Badge>
        <Badge>{roleLabel}</Badge>
        <Badge tone="success">{ecosystem}</Badge>
        <Badge>{concierge}</Badge>
        <Badge tone={status === "Operational" ? "success" : "warning"}>{status}</Badge>
        <button
          type="button"
          className="uws-link eds-type-small"
          onClick={() => {
            void telemetry.userActivity("uws_open_search");
            openPalette();
          }}
        >
          Search · ⌘K
        </button>
        <button
          type="button"
          className="uws-link eds-type-small"
          onClick={() => {
            void telemetry.userActivity("uws_quick_switch");
            openQuickSwitcher();
          }}
        >
          Switch · Ctrl+Tab
        </button>
      </div>

      <nav className="uws-switch" aria-label="Global quick switch">
        {GLOBAL_QUICK_SWITCH.map((item) => {
          const active =
            loc.pathname === item.route ||
            (item.route !== "/dashboard" && loc.pathname.startsWith(item.route.split("?")[0]!));
          return (
            <Link
              key={item.id}
              to={item.route}
              className={`uws-chip${active ? " is-active" : ""}`}
              onClick={() => void telemetry.userActivity(`uws_switch:${item.id}`)}
            >
              <span className="uws-chip-hint">{item.hint}</span>
              {item.label}
            </Link>
          );
        })}
        <Button
          size="sm"
          variant="ghost"
          className="eds-anim-micro"
          onClick={() => {
            void telemetry.userActivity("uws_commands");
            openOmnibox();
          }}
        >
          Commands · ⌘/
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="eds-anim-micro"
          onClick={() => navigate("/platform-builder/concierge")}
        >
          Concierge
        </Button>
      </nav>
    </div>
  );
}
