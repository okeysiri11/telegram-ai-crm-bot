import { useWorkspaceNavigation } from "@/workspace-engine/useWorkspaceTabs";
import { useNotificationStore } from "@/notifications/notificationStore";
import { logActivity } from "@/workspace-engine/activityJournal";
import { Button, Card } from "@/ui";

export type UniversalAction = {
  id: string;
  label: string;
  route: string;
  group: "create" | "open";
};

export const UNIVERSAL_QUICK_ACTIONS: UniversalAction[] = [
  { id: "ua_client", label: "New Client", route: "/crm?action=create_client", group: "create" },
  { id: "ua_project", label: "New Project", route: "/projects?action=create_project", group: "create" },
  { id: "ua_task", label: "New Task", route: "/projects?action=create_task", group: "create" },
  { id: "ua_wf", label: "New Workflow", route: "/automation?action=create_workflow", group: "create" },
  { id: "ua_agent", label: "New AI Agent", route: "/ai-agents?action=create", group: "create" },
  { id: "ua_doc", label: "Upload Document", route: "/documents?action=create_document", group: "create" },
  { id: "ua_dash", label: "Open Dashboard", route: "/dashboard", group: "open" },
  { id: "ua_crm", label: "Open CRM", route: "/crm", group: "open" },
  { id: "ua_erp", label: "Open ERP", route: "/erp", group: "open" },
];

/** Launch create/open actions from Command Center / anywhere shell. */
export function UniversalQuickActionsBar({ compact = false }: { compact?: boolean }) {
  const { open } = useWorkspaceNavigation();
  const push = useNotificationStore((s) => s.push);

  function run(a: UniversalAction) {
    logActivity({
      kind: a.group === "create" ? "create" : "navigate",
      title: a.label,
      detail: a.route,
    });
    if (a.group === "create") {
      push({
        kind: "success",
        title: a.label,
        body: "Launched from Universal Quick Actions",
        level: "success",
      });
    }
    open(a.route);
  }

  const body = (
    <div className={compact ? "flex flex-wrap gap-2" : "grid gap-2 sm:grid-cols-2 lg:grid-cols-3"}>
      {UNIVERSAL_QUICK_ACTIONS.map((a) => (
        <Button
          key={a.id}
          size="sm"
          variant={a.group === "create" ? "primary" : "secondary"}
          className="justify-start"
          onClick={() => run(a)}
        >
          {a.label}
        </Button>
      ))}
    </div>
  );

  if (compact) return <div aria-label="Universal quick actions">{body}</div>;

  return <Card title="Universal Quick Actions">{body}</Card>;
}
