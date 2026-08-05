/**
 * Window frame — Sprint 27.7 / 28.4.
 * Move · resize · snap preview · tabs · split · fullscreen chrome.
 */

import { useRef, type CSSProperties, type MouseEvent as ReactMouseEvent } from "react";
import type { DesktopWindowState } from "./types";
import { useDesktopStore } from "./desktopStore";

type Props = {
  win: DesktopWindowState;
};

export function WindowFrame({ win }: Props) {
  const focusWindow = useDesktopStore((s) => s.focusWindow);
  const closeWindow = useDesktopStore((s) => s.closeWindow);
  const minimizeWindow = useDesktopStore((s) => s.minimizeWindow);
  const toggleMaximize = useDesktopStore((s) => s.toggleMaximize);
  const setFullscreen = useDesktopStore((s) => s.setFullscreen);
  const snapWindow = useDesktopStore((s) => s.snapWindow);
  const centerRestore = useDesktopStore((s) => s.centerRestore);
  const moveWindow = useDesktopStore((s) => s.moveWindow);
  const resizeWindow = useDesktopStore((s) => s.resizeWindow);
  const persist = useDesktopStore((s) => s.persist);
  const focusedId = useDesktopStore((s) => s.focusedId);
  const detectSnapFromPoint = useDesktopStore((s) => s.detectSnapFromPoint);
  const setSnapPreview = useDesktopStore((s) => s.setSnapPreview);
  const activateTab = useDesktopStore((s) => s.activateTab);
  const closeTab = useDesktopStore((s) => s.closeTab);
  const pinTab = useDesktopStore((s) => s.pinTab);
  const duplicateTab = useDesktopStore((s) => s.duplicateTab);
  const detachTab = useDesktopStore((s) => s.detachTab);
  const reorderTabs = useDesktopStore((s) => s.reorderTabs);
  const setSplit = useDesktopStore((s) => s.setSplit);
  const drag = useRef<{ ox: number; oy: number; sx: number; sy: number } | null>(null);
  const resize = useRef<{ ow: number; oh: number; ox: number; oy: number; sx: number; sy: number; edge: string } | null>(
    null,
  );
  const tabDrag = useRef<number | null>(null);

  if (win.minimized) return null;

  const focused = focusedId === win.id;
  const isMax = win.maximized || win.fullscreen || win.mode === "maximized" || win.mode === "fullscreen";
  const style: CSSProperties = isMax
    ? { left: 0, top: 0, width: "100%", height: "calc(100% - 4rem)", zIndex: win.zIndex }
    : {
        left: win.x,
        top: win.y,
        width: win.width,
        height: win.height,
        zIndex: win.zIndex,
      };

  function onTitleDown(e: ReactMouseEvent) {
    if (isMax) return;
    e.preventDefault();
    focusWindow(win.id);
    drag.current = { ox: win.x, oy: win.y, sx: e.clientX, sy: e.clientY };
    function onMove(ev: MouseEvent) {
      if (!drag.current) return;
      moveWindow(
        win.id,
        drag.current.ox + (ev.clientX - drag.current.sx),
        drag.current.oy + (ev.clientY - drag.current.sy),
      );
      setSnapPreview(detectSnapFromPoint(ev.clientX, ev.clientY));
    }
    function onUp(ev: MouseEvent) {
      const preview = detectSnapFromPoint(ev.clientX, ev.clientY);
      drag.current = null;
      setSnapPreview(null);
      if (preview) snapWindow(win.id, preview.region);
      else persist();
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  function onResizeDown(e: ReactMouseEvent, edge = "se") {
    if (isMax) return;
    e.preventDefault();
    e.stopPropagation();
    focusWindow(win.id);
    resize.current = {
      ow: win.width,
      oh: win.height,
      ox: win.x,
      oy: win.y,
      sx: e.clientX,
      sy: e.clientY,
      edge,
    };
    function onMove(ev: MouseEvent) {
      if (!resize.current) return;
      const dx = ev.clientX - resize.current.sx;
      const dy = ev.clientY - resize.current.sy;
      let width = resize.current.ow;
      let height = resize.current.oh;
      let x = resize.current.ox;
      let y = resize.current.oy;
      if (edge.includes("e")) width = resize.current.ow + dx;
      if (edge.includes("s")) height = resize.current.oh + dy;
      if (edge.includes("w")) {
        width = resize.current.ow - dx;
        x = resize.current.ox + dx;
      }
      if (edge.includes("n")) {
        height = resize.current.oh - dy;
        y = resize.current.oy + dy;
      }
      resizeWindow(win.id, width, height, x, y);
    }
    function onUp() {
      resize.current = null;
      persist();
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  const tabs = win.tabs || [];
  const active = tabs.find((t) => t.id === win.activeTabId) || tabs[0];
  const embedSrc = `${active?.path || win.path}${(active?.path || win.path).includes("?") ? "&" : "?"}embed=1`;
  const secondary = win.split
    ? tabs.find((t) => t.id === win.splitSecondaryTabId) || tabs.find((t) => t.id !== win.activeTabId)
    : null;
  const secondarySrc = secondary
    ? `${secondary.path}${secondary.path.includes("?") ? "&" : "?"}embed=1`
    : null;

  return (
    <div
      className={`edt-window edm-overlay-panel${focused ? " is-focused" : ""}${win.mode === "snapped" ? " is-snapped" : ""}`}
      style={style}
      role="dialog"
      aria-label={win.title}
      data-mode={win.mode || "floating"}
      onMouseDown={() => focusWindow(win.id)}
    >
      <header className="edt-window-titlebar" onMouseDown={onTitleDown} onDoubleClick={() => toggleMaximize(win.id)}>
        <div className="edt-window-traffic">
          <button type="button" className="edt-traffic edt-traffic--close" aria-label="Close" onClick={() => closeWindow(win.id)} />
          <button type="button" className="edt-traffic edt-traffic--min" aria-label="Minimize" onClick={() => minimizeWindow(win.id)} />
          <button type="button" className="edt-traffic edt-traffic--max" aria-label="Maximize" onClick={() => toggleMaximize(win.id)} />
        </div>
        <p className="edt-window-title">{win.title}</p>
        <div className="edt-window-actions">
          <button type="button" aria-label="Snap left" onClick={() => snapWindow(win.id, "left")}>
            ◂
          </button>
          <button type="button" aria-label="Snap right" onClick={() => snapWindow(win.id, "right")}>
            ▸
          </button>
          <button type="button" aria-label="Snap top" onClick={() => snapWindow(win.id, "top")}>
            ▴
          </button>
          <button type="button" aria-label="Snap bottom" onClick={() => snapWindow(win.id, "bottom")}>
            ▾
          </button>
          <button type="button" aria-label="Quarter top-left" onClick={() => snapWindow(win.id, "top-left")}>
            ⌜
          </button>
          <button type="button" aria-label="Center restore" onClick={() => centerRestore(win.id)}>
            ▣
          </button>
          <button type="button" aria-label="Fullscreen" onClick={() => setFullscreen(win.id)}>
            ⛶
          </button>
          <button
            type="button"
            aria-label="Split view"
            onClick={() => setSplit(win.id, win.split ? null : "vertical")}
          >
            ⧉
          </button>
        </div>
      </header>

      {tabs.length > 0 ? (
        <div className="edt-window-tabs" role="tablist" aria-label="Window tabs">
          {tabs.map((t, idx) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={t.id === win.activeTabId}
              className={`edt-window-tab${t.id === win.activeTabId ? " is-active" : ""}${t.pinned ? " is-pinned" : ""}`}
              draggable
              onDragStart={() => {
                tabDrag.current = idx;
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => {
                if (tabDrag.current == null) return;
                reorderTabs(win.id, tabDrag.current, idx);
                tabDrag.current = null;
              }}
              onClick={() => activateTab(win.id, t.id)}
              onDoubleClick={() => pinTab(win.id, t.id)}
              onContextMenu={(e) => {
                e.preventDefault();
                duplicateTab(win.id, t.id);
              }}
            >
              <span>{t.pinned ? "📌 " : ""}{t.title}</span>
              <span
                className="edt-window-tab-x"
                role="button"
                tabIndex={0}
                aria-label={`Close ${t.title}`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (tabs.length <= 1) closeWindow(win.id);
                  else closeTab(win.id, t.id);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.stopPropagation();
                    if (tabs.length <= 1) closeWindow(win.id);
                    else closeTab(win.id, t.id);
                  }
                }}
              >
                ×
              </span>
              {tabs.length > 1 ? (
                <span
                  className="edt-window-tab-detach"
                  role="button"
                  tabIndex={0}
                  aria-label={`Detach ${t.title}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    detachTab(win.id, t.id);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.stopPropagation();
                      detachTab(win.id, t.id);
                    }
                  }}
                >
                  ↗
                </span>
              ) : null}
            </button>
          ))}
        </div>
      ) : null}

      <div className={`edt-window-body${win.split ? ` is-split is-split--${win.split}` : ""}`}>
        <iframe title={win.title} src={embedSrc} className="edt-window-frame" loading="lazy" />
        {win.split && secondarySrc ? (
          <iframe title={`${win.title} split`} src={secondarySrc} className="edt-window-frame" loading="lazy" />
        ) : null}
      </div>

      {!isMax ? (
        <>
          <div className="edt-window-resize edt-window-resize--se" onMouseDown={(e) => onResizeDown(e, "se")} aria-hidden />
          <div className="edt-window-resize edt-window-resize--e" onMouseDown={(e) => onResizeDown(e, "e")} aria-hidden />
          <div className="edt-window-resize edt-window-resize--s" onMouseDown={(e) => onResizeDown(e, "s")} aria-hidden />
          <div className="edt-window-resize edt-window-resize--w" onMouseDown={(e) => onResizeDown(e, "w")} aria-hidden />
          <div className="edt-window-resize edt-window-resize--n" onMouseDown={(e) => onResizeDown(e, "n")} aria-hidden />
        </>
      ) : null}
    </div>
  );
}
