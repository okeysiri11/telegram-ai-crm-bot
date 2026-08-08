import type { MouseEvent as ReactMouseEvent, ReactNode } from "react";
import { useRef } from "react";
import { Button } from "@/ui";
import { useI18n } from "@/i18n";
import { useShellLayoutStore, type DockSide } from "./shellLayoutStore";

type DockPanelProps = {
  side: DockSide;
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  /** Sprint 41.3 — Activity Center: no manual resize. */
  resizable?: boolean;
};

/**
 * Sprint 27.4 / 41.3 — dockable panel: collapse, pin, auto-hide; optional resize.
 */
export function DockPanel({
  side,
  title,
  subtitle,
  children,
  className = "",
  resizable,
}: DockPanelProps) {
  const t = useI18n((s) => s.t);
  const dock = useShellLayoutStore((s) => s.docks[side]);
  const toggleDockCollapse = useShellLayoutStore((s) => s.toggleDockCollapse);
  const toggleDockPin = useShellLayoutStore((s) => s.toggleDockPin);
  const toggleDockAutoHide = useShellLayoutStore((s) => s.toggleDockAutoHide);
  const resizeDock = useShellLayoutStore((s) => s.resizeDock);
  const setDock = useShellLayoutStore((s) => s.setDock);
  const dragStart = useRef<{ x: number; y: number; size: number } | null>(null);
  const allowResize = resizable ?? side !== "right";

  if (!dock.open) return null;

  if (dock.collapsed) {
    return (
      <aside
        className={`ews-dock ews-dock--${side} ews-dock--collapsed ews-dock--anim ews-glass ${className}`}
        aria-label={`${title} — свёрнуто`}
        onMouseEnter={() => {
          if (dock.autoHide) setDock(side, { collapsed: false });
        }}
      >
        <Button
          size="sm"
          variant="ghost"
          className="ews-dock-expand"
          onClick={() => toggleDockCollapse(side)}
          aria-label={t("dock.expand")}
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
    if (!allowResize) return;
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
      className={`ews-dock ews-dock--${side} ews-dock--anim ews-glass ${className}`}
      style={sizeStyle}
      aria-label={title}
      onMouseLeave={() => {
        if (dock.autoHide && !dock.pinned) setDock(side, { collapsed: true });
      }}
    >
      {allowResize ? (
        <div
          className={`ews-dock-resize ews-dock-resize--${side}`}
          onMouseDown={onResizeStart}
          role="separator"
          aria-orientation={side === "bottom" ? "horizontal" : "vertical"}
          aria-label={t("dock.resize")}
        />
      ) : null}
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
            aria-label={dock.pinned ? t("iface.panel.unpin") : t("iface.panel.pin")}
            onClick={() => toggleDockPin(side)}
          >
            {dock.pinned ? t("dock.pinned") : t("dock.pin")}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            aria-pressed={dock.autoHide}
            aria-label={t("iface.panel.autoHide")}
            onClick={() => toggleDockAutoHide(side)}
          >
            {dock.autoHide ? t("dock.auto") : t("dock.hold")}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => toggleDockCollapse(side)}
            aria-label={t("dock.collapse")}
          >
            {side === "bottom" ? "▾" : side === "left" ? "◂" : "▸"}
          </Button>
        </div>
      </div>
      <div className="ews-dock-body">{children}</div>
    </aside>
  );
}
