import { useEffect, useRef, useState } from "react";
import { Button } from "@/ui";
import { ENTERPRISE_QUICK_CREATE, runQuickCreate } from "@/workspace-engine/quickCreateCatalog";
import { useWorkspaceNavigation } from "@/workspace-engine/useWorkspaceTabs";
import { useNotificationStore } from "@/notifications/notificationStore";
import { logActivity } from "@/workspace-engine/activityJournal";

/**
 * Sprint 27.4 — universal Quick Create FAB (Client, Project, Task, Document, Agent, …).
 */
export function QuickCreateButton() {
  const [open, setOpen] = useState(false);
  const { open: openTab } = useWorkspaceNavigation();
  const push = useNotificationStore((s) => s.push);
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <div className="ews-quick-create" ref={panelRef}>
      {open ? (
        <div className="ews-quick-create-menu ews-glass" role="menu" aria-label="Quick Create">
          <p className="eds-type-section px-2 pt-2">Create</p>
          {ENTERPRISE_QUICK_CREATE.map((a) => (
            <button
              key={a.id}
              type="button"
              role="menuitem"
              className="ews-quick-create-item"
              onClick={() => {
                runQuickCreate(a, { openTab, push, logActivity });
                setOpen(false);
              }}
            >
              <span className="font-medium">{a.label}</span>
              <span className="eds-type-helper">{a.entity}</span>
            </button>
          ))}
        </div>
      ) : null}
      <Button
        size="sm"
        variant="primary"
        className="ews-quick-create-fab"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((v) => !v)}
      >
        + Create
      </Button>
    </div>
  );
}
