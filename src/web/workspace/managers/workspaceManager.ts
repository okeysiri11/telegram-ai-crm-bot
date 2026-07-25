import type { WorkspaceRecord } from "../types";

const workspaces: WorkspaceRecord[] = [
  {
    workspaceId: "ws_personal",
    name: "My Workspace",
    owner: "usr_owner",
    organization: "demo-corp",
    kind: "personal",
    activeModules: ["hub", "ai", "workflow", "crm", "analytics"],
    layout: "layout_personal",
    permissions: ["read", "write", "admin"],
    theme: "system",
    status: "active",
  },
  {
    workspaceId: "ws_team_ops",
    name: "Ops Team",
    owner: "usr_ops",
    organization: "demo-corp",
    kind: "team",
    activeModules: ["workflow", "erp", "notifications"],
    layout: "layout_ops",
    permissions: ["read", "write"],
    theme: "light",
    status: "active",
  },
  {
    workspaceId: "ws_dept_finance",
    name: "Finance Department",
    owner: "usr_owner",
    organization: "demo-corp",
    kind: "department",
    activeModules: ["finance", "analytics", "reports"],
    layout: "layout_finance",
    permissions: ["read", "write"],
    theme: "corporate",
    status: "active",
  },
  {
    workspaceId: "ws_org",
    name: "Demo Corp Org",
    owner: "usr_owner",
    organization: "demo-corp",
    kind: "organization",
    activeModules: ["hub", "crm", "erp", "marketplace", "ai"],
    layout: "layout_org",
    permissions: ["read", "admin"],
    theme: "dark",
    status: "active",
  },
  {
    workspaceId: "ws_project_web",
    name: "Enterprise Web Project",
    owner: "usr_owner",
    organization: "demo-corp",
    kind: "project",
    activeModules: ["ai", "workflow", "analytics"],
    layout: "layout_project",
    permissions: ["read", "write"],
    theme: "system",
    status: "active",
  },
];

let activeId = "ws_personal";

export const workspaceManager = {
  list(): WorkspaceRecord[] {
    return [...workspaces];
  },
  get(id: string) {
    return workspaces.find((w) => w.workspaceId === id);
  },
  active() {
    return this.get(activeId) || workspaces[0];
  },
  setActive(id: string) {
    if (workspaces.some((w) => w.workspaceId === id)) activeId = id;
    return this.active();
  },
  kinds() {
    return ["personal", "team", "department", "organization", "project"] as const;
  },
};
