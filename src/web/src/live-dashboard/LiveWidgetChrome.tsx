import type { ReactNode } from "react";
import { Button } from "@/ui";
import type { LiveWidgetId } from "./types";
import { useLiveDashboardStore } from "./liveDashboardStore";
import { widgetTitle } from "./liveDashboardCatalog";

type Props = {
  id: LiveWidgetId;
  colSpan: 1 | 2 | 3 | 4;
  collapsed: boolean;
  pinned: boolean;
  onRefresh?: () => void;
  children: ReactNode;
};

/** Reusable widget chrome — collapse · refresh · fullscreen · pin · resize. */
export function LiveWidgetChrome({ id, colSpan, collapsed, pinned, onRefresh, children }: Props) {
  const toggleCollapse = useLiveDashboardStore((s) => s.toggleCollapse);
  const togglePin = useLiveDashboardStore((s) => s.togglePin);
  const setFullscreen = useLiveDashboardStore((s) => s.setFullscreen);
  const resizeWidget = useLiveDashboardStore((s) => s.resizeWidget);
  const fullscreenId = useLiveDashboardStore((s) => s.fullscreenId);
  const isFs = fullscreenId === id;

  return (
    <article
      className={`eld-widget ews-glass${collapsed ? " is-collapsed" : ""}${pinned ? " is-pinned" : ""}${isFs ? " is-fullscreen" : ""}`}
      data-widget={id}
      draggable={!isFs}
      onDragStart={(e) => {
        e.dataTransfer.setData("text/eld-widget", id);
        e.dataTransfer.effectAllowed = "move";
      }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        const from = e.dataTransfer.getData("text/eld-widget") as LiveWidgetId;
        if (from) useLiveDashboardStore.getState().moveWidget(from, id);
      }}
    >
      <header className="eld-widget-head">
        <div className="eld-widget-title">
          {pinned ? <span aria-hidden>◆</span> : null}
          <h3>{widgetTitle(id)}</h3>
        </div>
        <div className="eld-widget-actions">
          <Button
            size="sm"
            variant="ghost"
            aria-label="Narrower"
            disabled={colSpan <= 1}
            onClick={() => resizeWidget(id, Math.max(1, colSpan - 1) as 1 | 2 | 3 | 4)}
          >
            −
          </Button>
          <Button
            size="sm"
            variant="ghost"
            aria-label="Wider"
            disabled={colSpan >= 4}
            onClick={() => resizeWidget(id, Math.min(4, colSpan + 1) as 1 | 2 | 3 | 4)}
          >
            +
          </Button>
          <Button size="sm" variant="ghost" aria-label="Refresh" onClick={() => onRefresh?.()}>
            ↻
          </Button>
          <Button
            size="sm"
            variant="ghost"
            aria-pressed={pinned}
            aria-label={pinned ? "Unpin" : "Pin"}
            onClick={() => togglePin(id)}
          >
            {pinned ? "Unpin" : "Pin"}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            aria-label={isFs ? "Exit fullscreen" : "Fullscreen"}
            onClick={() => setFullscreen(isFs ? null : id)}
          >
            {isFs ? "Exit" : "⛶"}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            aria-label={collapsed ? "Expand" : "Collapse"}
            onClick={() => toggleCollapse(id)}
          >
            {collapsed ? "▸" : "▾"}
          </Button>
        </div>
      </header>
      {!collapsed ? <div className="eld-widget-body">{children}</div> : null}
    </article>
  );
}
