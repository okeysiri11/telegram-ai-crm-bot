import { create } from "zustand";

export type Workspace = {
  company: string;
  department: string;
  project: string;
  userContext: string;
  permissions: string[];
  activeModules: string[];
};

type WorkspaceState = {
  workspace: Workspace;
  setWorkspace: (patch: Partial<Workspace>) => void;
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  workspace: {
    company: "demo-corp",
    department: "operations",
    project: "enterprise-web",
    userContext: "owner",
    permissions: ["read", "write", "admin"],
    activeModules: ["hub", "workflow", "ai", "knowledge", "marketplace"],
  },
  setWorkspace: (patch) =>
    set((s) => ({ workspace: { ...s.workspace, ...patch } })),
}));
