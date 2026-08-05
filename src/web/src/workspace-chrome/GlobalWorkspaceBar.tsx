/**
 * Global Workspace chrome — Sprint 32.3.6 / 30.2 Russian.
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
import { useI18n } from "@/i18n";
import { useRoleSwitcher, resolveRoleLabel } from "@/navigation/roleSwitcherStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { ORG_SELECTOR_OPTIONS, ROLE_SWITCHER_OPTIONS } from "@/navigation/enterpriseRuNav";

export function GlobalWorkspaceBar() {
  const t = useI18n((s) => s.t);
  const loc = useLocation();
  const navigate = useNavigate();
  const { openPalette, openQuickSwitcher } = useNavigationUi();
  const { openOmnibox } = useCommandCenterUi();
  const user = useAuthStore((s) => s.user);
  const ws = useWorkspaceStore((s) => s.workspace);
  const first = loadFirstEntry();
  const role = firstEntryRoleCatalog.get(first.roleId);
  const switcherRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const switcherLabel = ROLE_SWITCHER_OPTIONS.find((o) => o.id === switcherRoleId)?.label;
  const roleLabel =
    switcherLabel ||
    role?.label ||
    resolveRoleLabel(user?.roleId) ||
    user?.roles?.[0] ||
    ws.userContext ||
    "Сотрудник";
  const orgId = useOrgSelector((s) => s.organizationId);
  const company =
    ORG_SELECTOR_OPTIONS.find((o) => o.id === orgId)?.label ||
    first.companyName ||
    ws.company;
  const ecosystem = detectActiveEcosystem(loc.pathname) || "Платформа";
  const concierge = first.conciergeName || t("uws.concierge");
  const status = workspaceStatusLabel(ws.activeModules);

  return (
    <div className="uws-chrome eds-anim-fade">
      <div className="uws-context" aria-label="Контекст рабочего пространства">
        <Badge>{company}</Badge>
        <Badge>{ws.project || "пространство"}</Badge>
        <Badge>{roleLabel}</Badge>
        <Badge tone="success">{ecosystem}</Badge>
        <Badge>{concierge}</Badge>
        <Badge tone={status === "В работе" ? "success" : "warning"}>{status}</Badge>
        <button
          type="button"
          className="uws-link eds-type-small"
          onClick={() => {
            void telemetry.userActivity("uws_open_search");
            openPalette();
          }}
        >
          {t("uws.search")}
        </button>
        <button
          type="button"
          className="uws-link eds-type-small"
          onClick={() => {
            void telemetry.userActivity("uws_quick_switch");
            openQuickSwitcher();
          }}
        >
          {t("uws.switch")}
        </button>
      </div>

      <nav className="uws-switch" aria-label="Быстрое переключение">
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
          {t("uws.commands")}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="eds-anim-micro"
          onClick={() => navigate("/platform-builder/concierge")}
        >
          {t("uws.concierge")}
        </Button>
      </nav>
    </div>
  );
}
