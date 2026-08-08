import { Link } from "react-router-dom";
import { Card } from "@/ui";
import { logActivity } from "./activityJournal";
import { useWorkspaceNavigation } from "./useWorkspaceTabs";
import { useNotificationStore } from "@/notifications/notificationStore";
import { RU_QUICK_ACTIONS } from "@/navigation/enterpriseRuNav";
import { isRouteAllowedForViewMode, useViewModeStore } from "@/ux-revolution";

export type QuickActionDef = {
  id: string;
  label: string;
  route: string;
  kind: "create" | "open";
};

export const ENTERPRISE_QUICK_ACTIONS: QuickActionDef[] = [
  ...RU_QUICK_ACTIONS.map((a) => ({
    id: a.id,
    label: a.label,
    route: a.route,
    kind: (a.id === "qa_map" || a.id === "qa_ai" ? "open" : "create") as "create" | "open",
  })),
  { id: "qa_wf", label: "Создать процесс", route: "/automation?action=create_workflow", kind: "create" },
  { id: "qa_kb", label: "Создать знание", route: "/knowledge?action=create", kind: "create" },
  { id: "qa_company", label: "Создать компанию", route: "/identity/organizations?action=create_company", kind: "create" },
];

export function QuickActionsPanel({ compact = false }: { compact?: boolean }) {
  const { open } = useWorkspaceNavigation();
  const push = useNotificationStore((s) => s.push);
  const viewMode = useViewModeStore((s) => s.viewMode);
  const actions = ENTERPRISE_QUICK_ACTIONS.filter((a) => isRouteAllowedForViewMode(a.route, viewMode));

  return (
    <Card title="Быстрые действия">
      <div className={compact ? "grid gap-2 sm:grid-cols-2" : "grid gap-2 sm:grid-cols-2 lg:grid-cols-3"}>
        {actions.map((a) => (
          <button
            key={a.id}
            type="button"
            className="cc-action text-left"
            onClick={() => {
              logActivity({ kind: "create", title: a.label, detail: a.route });
              push({
                kind: "success",
                title: a.label,
                body: "Действие зарегистрировано в рабочем пространстве",
                level: "success",
              });
              open(a.route);
            }}
          >
            <span className="font-medium">{a.label}</span>
          </button>
        ))}
      </div>
      {!compact ? (
        <p className="mt-2 eds-type-helper">
          Также доступно через палитру команд ·{" "}
          <Link to="/search" className="text-[var(--eds-primary)]">
            Рабочее пространство поиска
          </Link>
        </p>
      ) : null}
    </Card>
  );
}
