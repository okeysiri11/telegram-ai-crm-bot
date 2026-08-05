import type { MouseEvent as ReactMouseEvent, ReactNode } from "react";
import { useRef } from "react";
import { Button } from "@/ui";
import { useShellLayoutStore, type DockSide } from "./shellLayoutStore";

type DockPanelProps = {
  side: DockSide;
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
};

/**
 * Sprint 27.4 — dockable panel chrome: collapse, resize, pin, auto-hide.
 */
export function DockPanel({ side, title, subtitle, children, className = "" }: DockPanelProps) {
  const dock = useShellLayoutStore((s) => s.docks[side]);
  const toggleDockCollapse = useShellLayoutStore((s) => s.toggleDockCollapse);
  const toggleDockPin = useShellLayoutStore((s) => s.toggleDockPin);
  const toggleDockAutoHide = useShellLayoutStore((s) => s.toggleDockAutoHide);
  const resizeDock = useShellLayoutStore((s) => s.resizeDock);
  const setDock = useShellLayoutStore((s) => s.setDock);
  const dragStart = useRef<{ x: number; y: number; size: number } | null>(null);

  if (!dock.open) return null;

  if (dock.collapsed) {
    return (
      <aside
        className={`ews-dock ews-dock--${side} ews-dock--collapsed ews-glass ${className}`}
        aria-label={`${title} collapsed`}
        onMouseEnter={() => {
          if (dock.autoHide) setDock(side, { collapsed: false });
        }}
      >
        <Button
          size="sm"
          variant="ghost"
          className="ews-dock-expand"
          onClick={() => toggleDockCollapse(side)}
          aria-label={`Expand ${title}`}
        >
          {side === "left" ? "▸" : side === "right" ? "◂" : "▴"}
        </Button>
      </aside>
    );
  }

  const sizeStyle =
    side === "bottom"
      ? ({ height: dock.size } as const)
      : ({ width: dock.size } as const);

  function onResizeStart(e: ReactMouseEvent) {
    e.preventDefault();
    dragStart.current = { x: e.clientX, y: e.clientY, size: dock.size };
    function onMove(ev: MouseEvent) {
      if (!dragStart.current) return;
      if (side === "left") {
        resizeDock(side, dragStart.current.size + (ev.clientX - dragStart.current.x));
      } else if (side === "right") {
        resizeDock(side, dragStart.current.size - (ev.clientX - dragStart.current.x));
      } else {
        resizeDock(side, dragStart.current.size - (ev.clientY - dragStart.current.y));
      }
    }
    function onUp() {
      dragStart.current = null;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  return (
    <aside
      className={`ews-dock ews-dock--${side} ews-glass ${className}`}
      style={sizeStyle}
      aria-label={title}
      onMouseLeave={() => {
        if (dock.autoHide && !dock.pinned) setDock(side, { collapsed: true });
      }}
    >
      <div
        className={`ews-dock-resize ews-dock-resize--${side}`}
        onMouseDown={onResizeStart}
        role="separator"
        aria-orientation={side === "bottom" ? "horizontal" : "vertical"}
        aria-label={`Resize ${title}`}
      />
      <div className="ews-dock-head">
        <div>
          <p className="eds-type-section">{title}</p>
          {subtitle ? <p className="eds-type-helper">{subtitle}</p> : null}
        </div>
        <div className="ews-dock-actions">
          <Button
            size="sm"
            variant="ghost"
            aria-pressed={dock.pinned}
            aria-label={dock.pinned ? "Unpin panel" : "Pin panel"}
            onClick={() => toggleDockPin(side)}
          >
            {dock.pinned ? "Pinned" : "Pin"}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            aria-pressed={dock.autoHide}
            aria-label={dock.autoHide ? "Disable auto-hide" : "Enable auto-hide"}
            onClick={() => toggleDockAutoHide(side)}
          >
            {dock.autoHide ? "Auto" : "Hold"}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => toggleDockCollapse(side)} aria-label={`Collapse ${title}`}>
            {side === "bottom" ? "▾" : side === "left" ? "◂" : "▸"}
          </Button>
        </div>
      </div>
      <div className="ews-dock-body">{children}</div>
    </aside>
  );
}
