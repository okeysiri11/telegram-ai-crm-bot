import type { WorkspaceKind, FederatedWorkspace } from "../types";

const WORKSPACES: FederatedWorkspace[] = [
  { id: "ws_personal", kind: "personal", name: "Personal Workspace", route: "/workspace?scope=personal" },
  { id: "ws_org", kind: "organization", name: "Organization Workspace", route: "/workspace?scope=organization" },
  { id: "ws_dept", kind: "department", name: "Department Workspace", route: "/workspace?scope=department" },
  { id: "ws_project", kind: "project", name: "Project Workspace", route: "/workspace?scope=project" },
  { id: "ws_customer", kind: "customer", name: "Customer Workspace", route: "/workspace?scope=customer" },
  { id: "ws_ai", kind: "ai", name: "AI Workspace", route: "/workspace?scope=ai" },
  { id: "ws_temp", kind: "temporary", name: "Temporary Workspace", route: "/workspace?scope=temporary" },
];

let current: WorkspaceKind = "personal";

export const workspaceFederation = {
  kinds(): WorkspaceKind[] {
    return WORKSPACES.map((w) => w.kind);
  },
  list(): FederatedWorkspace[] {
    return [...WORKSPACES];
  },
  current(): FederatedWorkspace {
    return WORKSPACES.find((w) => w.kind === current) ?? WORKSPACES[0]!;
  },
  switchTo(kindOrId: string): FederatedWorkspace | null {
    const ws = WORKSPACES.find((w) => w.kind === kindOrId || w.id === kindOrId);
    if (!ws) return null;
    current = ws.kind;
    return ws;
  },
};
