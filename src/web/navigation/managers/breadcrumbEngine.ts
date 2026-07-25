import type { BreadcrumbPart } from "../types";

export const breadcrumbEngine = {
  fromPath(pathname: string): BreadcrumbPart[] {
    const parts = pathname.split("/").filter(Boolean);
    if (parts.length === 0) {
      return [{ label: "Workspace", path: "/workspace", level: "workspace" }];
    }
    const crumbs: BreadcrumbPart[] = [{ label: "Workspace", path: "/workspace", level: "workspace" }];
    let acc = "";
    parts.forEach((part, index) => {
      acc += `/${part}`;
      const level =
        index === 0 ? "module" : index === 1 ? "section" : index === 2 ? "page" : "entity";
      crumbs.push({
        label: part.replace(/[-_]/g, " "),
        path: acc,
        level: level as BreadcrumbPart["level"],
      });
    });
    return crumbs;
  },
};
