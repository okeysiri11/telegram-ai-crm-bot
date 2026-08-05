/**
 * Workspace profiles & templates — Sprint 28.4.
 * Persisted inside desktop session (no second storage engine).
 */

import type {
  DesktopWindowState,
  WorkspaceProfile,
  WorkspaceTemplateId,
  WallpaperId,
  DesktopLayoutId,
  DockItem,
} from "./types";
import { defaultDock } from "./desktopCatalog";

export const WORKSPACE_TEMPLATES: {
  id: WorkspaceTemplateId;
  name: string;
  description: string;
  appIds: string[];
  wallpaperId: WallpaperId;
  layoutId: DesktopLayoutId;
}[] = [
  {
    id: "blank",
    name: "Blank",
    description: "Empty desktop",
    appIds: [],
    wallpaperId: "aurora",
    layoutId: "default",
  },
  {
    id: "ops",
    name: "Operations",
    description: "Dashboard · CRM · Production Runtime",
    appIds: ["dashboard", "crm", "prod_runtime"],
    wallpaperId: "slate",
    layoutId: "ops",
  },
  {
    id: "creative",
    name: "Creative Studio",
    description: "AI Studio · Image · Video · Prompt",
    appIds: ["ai_studio", "prod_image", "prod_video", "prod_prompt"],
    wallpaperId: "studio",
    layoutId: "default",
  },
  {
    id: "dev",
    name: "Developer",
    description: "Command Center · Agent Studio · Workflow",
    appIds: ["devtools", "agent_studio", "workflow_studio"],
    wallpaperId: "midnight",
    layoutId: "dev",
  },
  {
    id: "executive",
    name: "Executive",
    description: "Dashboard · City · Analytics",
    appIds: ["dashboard", "city", "analytics"],
    wallpaperId: "aurora",
    layoutId: "sales",
  },
];

export function seedWorkspaceProfiles(): WorkspaceProfile[] {
  const now = new Date().toISOString();
  return [
    {
      id: "wp_default",
      name: "Default session",
      templateId: "blank",
      windows: [],
      focusedId: null,
      dock: defaultDock(),
      wallpaperId: "aurora",
      layoutId: "default",
      updatedAt: now,
    },
  ];
}

export function cloneWindows(windows: DesktopWindowState[]): DesktopWindowState[] {
  return windows.map((w) => ({
    ...w,
    tabs: w.tabs?.map((t) => ({ ...t })),
    closedTabStack: w.closedTabStack?.map((t) => ({ ...t })),
    restore: w.restore ? { ...w.restore } : undefined,
  }));
}

export function profileFromState(input: {
  id: string;
  name: string;
  templateId?: string;
  windows: DesktopWindowState[];
  focusedId: string | null;
  dock: DockItem[];
  wallpaperId: WallpaperId;
  layoutId: DesktopLayoutId;
}): WorkspaceProfile {
  return {
    id: input.id,
    name: input.name,
    templateId: input.templateId,
    windows: cloneWindows(input.windows),
    focusedId: input.focusedId,
    dock: input.dock.map((d) => ({ ...d })),
    wallpaperId: input.wallpaperId,
    layoutId: input.layoutId,
    updatedAt: new Date().toISOString(),
  };
}
