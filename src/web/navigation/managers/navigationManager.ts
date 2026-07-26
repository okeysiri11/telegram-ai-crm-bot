import type { MenuItem, NavSurface } from "../types";
import { menuEngine } from "./menuEngine";

let config: Record<NavSurface, MenuItem[]> = {
  main: [],
  sidebar: [],
  top: [],
  context: [],
  module: [],
  workspace: [],
};

function surfacesFrom(all: MenuItem[]): Record<NavSurface, MenuItem[]> {
  return {
    main: all,
    sidebar: all.filter((m) =>
      ["core", "business", "intelligence", "platform", "ecosystems"].includes(m.group || ""),
    ),
    top: all.filter((m) => ["workspace", "identity", "settings"].includes(m.module)),
    context: all.flatMap((m) => m.children || []),
    module: all,
    workspace: all.filter((m) => m.module === "workspace" || m.group === "intelligence"),
  };
}

function bootstrap() {
  config = surfacesFrom(menuEngine.all());
}

bootstrap();

export const navigationManager = {
  surfaces(): NavSurface[] {
    return ["main", "sidebar", "top", "context", "module", "workspace"];
  },
  get(surface: NavSurface): MenuItem[] {
    return structuredClone(config[surface]);
  },
  /** Permission-aware navigation — reuses menuEngine.forTenant (no parallel menu). */
  forTenant(tenantId: string, permissions: string[], surface: NavSurface = "sidebar"): MenuItem[] {
    const filtered = menuEngine.forTenant(tenantId, permissions);
    return structuredClone(surfacesFrom(filtered)[surface]);
  },
  configure(surface: NavSurface, items: MenuItem[]) {
    config[surface] = structuredClone(items);
    return this.get(surface);
  },
  reload() {
    bootstrap();
  },
};
