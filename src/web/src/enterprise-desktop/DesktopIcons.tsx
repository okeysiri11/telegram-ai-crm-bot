import { useRef, type MouseEvent as ReactMouseEvent } from "react";
import { ShellIcon } from "@/shell/enterprise/ShellIcons";
import type { ShellIconId } from "@/shell/enterprise/enterpriseNav";
import { useDesktopStore } from "./desktopStore";
import { appByPath } from "./desktopCatalog";
import type { DesktopIcon } from "./types";

/** Desktop icons — apps, folders, shortcuts with drag & drop. */
export function DesktopIcons() {
  const icons = useDesktopStore((s) => s.icons);
  const moveIcon = useDesktopStore((s) => s.moveIcon);
  const openApp = useDesktopStore((s) => s.openApp);
  const persist = useDesktopStore((s) => s.persist);
  const drag = useRef<{ id: string; ox: number; oy: number; sx: number; sy: number } | null>(null);

  function onIconPointerDown(icon: DesktopIcon, e: ReactMouseEvent) {
    if (e.detail === 2) {
      if (icon.kind === "folder") {
        openApp("/documents");
        return;
      }
      openApp(icon.target.startsWith("/") ? icon.target : appByPath(icon.target)?.id || icon.target);
      return;
    }
    drag.current = { id: icon.id, ox: icon.x, oy: icon.y, sx: e.clientX, sy: e.clientY };
    function onMove(ev: MouseEvent) {
      if (!drag.current) return;
      moveIcon(
        drag.current.id,
        drag.current.ox + (ev.clientX - drag.current.sx),
        drag.current.oy + (ev.clientY - drag.current.sy),
      );
    }
    function onUp() {
      drag.current = null;
      persist();
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  return (
    <div className="edt-icons" aria-label="Desktop icons">
      {icons.map((icon) => {
        const app = icon.kind === "app" ? appByPath(icon.target) : null;
        return (
          <button
            key={icon.id}
            type="button"
            className="edt-icon"
            style={{ left: icon.x, top: icon.y }}
            onMouseDown={(e) => onIconPointerDown(icon, e)}
            title={`${icon.label} · double-click to open`}
          >
            <span className="edt-icon-glyph" aria-hidden>
              {icon.kind === "folder" ? (
                <ShellIcon id="documents" className="edt-icon-svg" />
              ) : icon.kind === "shortcut" ? (
                <span className="edt-icon-shortcut">↗</span>
              ) : (
                <ShellIcon id={(app?.icon || "dashboard") as ShellIconId} className="edt-icon-svg" />
              )}
            </span>
            <span className="edt-icon-label">{icon.label}</span>
          </button>
        );
      })}
    </div>
  );
}
