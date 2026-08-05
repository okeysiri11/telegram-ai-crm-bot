import type { BreadcrumbPart } from "../types";
import { labelForSegment } from "../../src/workspace-chrome/workspaceContext";

/**
 * Breadcrumb labels — Sprint 32.3.6.
 * Uses existing path routing + unified label map (no new nav engine).
 */
export const breadcrumbEngine = {
  fromPath(pathname: string): BreadcrumbPart[] {
    const parts = pathname.split("/").filter(Boolean);
    const crumbs: BreadcrumbPart[] = [{ label: "Главная", path: "/dashboard", level: "workspace" }];
    if (parts.length === 0) {
      return crumbs;
    }
    let acc = "";
    parts.forEach((part, index) => {
      acc += `/${part}`;
      const level =
        index === 0 ? "module" : index === 1 ? "section" : index === 2 ? "page" : "entity";
      crumbs.push({
        label: labelForSegment(part),
        path: acc,
        level: level as BreadcrumbPart["level"],
      });
    });
    return crumbs;
  },
};
