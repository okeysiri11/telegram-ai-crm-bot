import { useWorkspaceManager } from "./workspaceManagerStore";
import { useWorkspaceNavigation } from "./useWorkspaceTabs";
import { useEffect, useRef, useState } from "react";

type MenuState = { tabId: string; x: number; y: number } | null;

/** Professional multi-tab chrome — drag reorder, pin, duplicate, reopen closed. */
export function WorkspaceTabBar() {
  const tabs = useWorkspaceManager((s) => s.tabs);
  const activeTabId = useWorkspaceManager((s) => s.activeTabId);
  const closedTabs = useWorkspaceManager((s) => s.closedTabs);
  const togglePin = useWorkspaceManager((s) => s.togglePin);
  const reorderTabs = useWorkspaceManager((s) => s.reorderTabs);
  const duplicateTab = useWorkspaceManager((s) => s.duplicateTab);
  const reopenClosedTab = useWorkspaceManager((s) => s.reopenClosedTab);
  const { activate, close, open } = useWorkspaceNavigation();
  const [menu, setMenu] = useState<MenuState>(null);
  const dragId = useRef<string | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!menu) return;
    function onDoc(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenu(null);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menu]);

  if (!tabs.length) return null;

  return (
    <div className="ews-tabbar" role="tablist" aria-label="Workspace tabs">
      <div className="ews-tabbar-scroll">
        {tabs.map((tab) => {
          const active = tab.id === activeTabId;
          return (
            <div
              key={tab.id}
              role="tab"
              aria-selected={active}
              draggable
              className={`ews-tab${active ? " is-active" : ""}${tab.pinned ? " is-pinned" : ""}`}
              onDragStart={() => {
                dragId.current = tab.id;
              }}
              onDragOver={(e) => {
                e.preventDefault();
              }}
              onDrop={(e) => {
                e.preventDefault();
                if (dragId.current) reorderTabs(dragId.current, tab.id);
                dragId.current = null;
              }}
              onContextMenu={(e) => {
                e.preventDefault();
                setMenu({ tabId: tab.id, x: e.clientX, y: e.clientY });
              }}
            >
              <button type="button" className="ews-tab-main" onClick={() => activate(tab.id)} title={tab.path}>
                {tab.pinned ? (
                  <span className="ews-tab-pin" aria-hidden>
                    ◆
                  </span>
                ) : null}
                <span className="ews-tab-title">{tab.title}</span>
              </button>
              <button
                type="button"
                className="ews-tab-action"
                aria-label={tab.pinned ? "Unpin tab" : "Pin tab"}
                onClick={() => togglePin(tab.id)}
              >
                {tab.pinned ? "•" : "○"}
              </button>
              {!tab.pinned ? (
                <button
                  type="button"
                  className="ews-tab-action"
                  aria-label={`Close ${tab.title}`}
                  onClick={() => close(tab.id)}
                >
                  ×
                </button>
              ) : null}
            </div>
          );
        })}
      </div>
      <button
        type="button"
        className="ews-tab-new"
        aria-label="Reopen closed tab"
        title={closedTabs[0] ? `Reopen ${closedTabs[0].title}` : "No closed tabs"}
        disabled={!closedTabs.length}
        onClick={() => {
          const tab = reopenClosedTab();
          if (tab) activate(tab.id);
        }}
      >
        ↶
      </button>
      <button type="button" className="ews-tab-new" aria-label="Open Dashboard tab" onClick={() => open("/dashboard")}>
        +
      </button>

      {menu ? (
        <div
          ref={menuRef}
          className="ews-tab-menu"
          style={{ left: menu.x, top: menu.y }}
          role="menu"
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              activate(menu.tabId);
              setMenu(null);
            }}
          >
            Activate
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              togglePin(menu.tabId);
              setMenu(null);
            }}
          >
            Toggle pin
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              const tab = duplicateTab(menu.tabId);
              if (tab) activate(tab.id);
              setMenu(null);
            }}
          >
            Duplicate
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              close(menu.tabId);
              setMenu(null);
            }}
          >
            Close
          </button>
          <button
            type="button"
            role="menuitem"
            disabled={!closedTabs.length}
            onClick={() => {
              const tab = reopenClosedTab();
              if (tab) activate(tab.id);
              setMenu(null);
            }}
          >
            Reopen closed
          </button>
        </div>
      ) : null}
    </div>
  );
}
