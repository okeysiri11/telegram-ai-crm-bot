import type { QuickActionDef } from "./QuickActionsPanel";
import { ENTERPRISE_QUICK_ACTIONS } from "./QuickActionsPanel";

export type QuickCreateDef = QuickActionDef & {
  entity: string;
};

/** Universal create targets — Sprint 27.4 Quick Create. */
export const ENTERPRISE_QUICK_CREATE: QuickCreateDef[] = [
  { id: "qc_client", label: "Client", entity: "CRM", route: "/crm?action=create_client", kind: "create" },
  { id: "qc_project", label: "Project", entity: "Projects", route: "/projects?action=create_project", kind: "create" },
  { id: "qc_task", label: "Task", entity: "Projects", route: "/projects?action=create_task", kind: "create" },
  { id: "qc_doc", label: "Document", entity: "Documents", route: "/documents?action=create_document", kind: "create" },
  { id: "qc_agent", label: "AI Agent", entity: "AI", route: "/ai-agents?action=create", kind: "create" },
  { id: "qc_wf", label: "Workflow", entity: "Automation", route: "/automation?action=create_workflow", kind: "create" },
  { id: "qc_kb", label: "Knowledge Page", entity: "Knowledge", route: "/knowledge?action=create", kind: "create" },
  { id: "qc_company", label: "Company", entity: "Identity", route: "/identity/organizations?action=create_company", kind: "create" },
];

/** Keep dashboard Quick Actions panel in sync with create set (RU labels retained). */
export function syncQuickActionsFromCreate(): QuickActionDef[] {
  return ENTERPRISE_QUICK_ACTIONS;
}

type RunCtx = {
  openTab: (path: string) => unknown;
  push: (n: { kind: "success"; title: string; body: string; level: "success" }) => void;
  logActivity: (e: { kind: "create"; title: string; detail: string }) => void;
};

export function runQuickCreate(a: QuickCreateDef, ctx: RunCtx) {
  ctx.logActivity({ kind: "create", title: `Create ${a.label}`, detail: a.route });
  ctx.push({
    kind: "success",
    title: `Create ${a.label}`,
    body: `Opened ${a.entity} create flow`,
    level: "success",
  });
  ctx.openTab(a.route);
}
