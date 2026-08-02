/**
 * Sprint 33.2 — Collapsible nav group (accordion panel).
 */

import type { ReactNode } from "react";
import { ShellIcon, type ShellIconId } from "@/shell/enterprise";
import { cn } from "@/utils/cn";
import type { NavGroupId } from "./intelligentNavGroups";

export function NavAccordionGroup({
  id,
  label,
  icon,
  expanded,
  onToggle,
  children,
}: {
  id: NavGroupId;
  label: string;
  icon: ShellIconId;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <div className="ews-nav-group" data-group={id}>
      <button
        type="button"
        className="ews-nav-group__btn"
        aria-expanded={expanded}
        aria-controls={`nav-group-${id}`}
        id={`nav-group-btn-${id}`}
        onClick={onToggle}
      >
        <ShellIcon id={icon} />
        <span>{label}</span>
        <span className="ews-nav-group__chevron" aria-hidden>
          ›
        </span>
      </button>
      <div
        id={`nav-group-${id}`}
        role="region"
        aria-labelledby={`nav-group-btn-${id}`}
        className={cn("ews-nav-group__panel", expanded && "is-open")}
      >
        <div className="ews-nav-group__panel-inner">{children}</div>
      </div>
    </div>
  );
}
