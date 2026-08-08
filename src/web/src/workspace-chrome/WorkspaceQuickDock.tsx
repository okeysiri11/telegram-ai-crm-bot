/**
 * Sprint 42.0 — Workspace Dock: favourite modules with pin / close / reorder (DnD).
 */

import { useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useI18n } from "@/i18n";
import { cn } from "@/utils/cn";
import { useViewModeStore, isRouteAllowedForViewMode } from "@/ux-revolution";
import { Button } from "@/ui";
import {
  DOCK_CATALOG,
  useWorkspaceDockStore,
  type DockFavourite,
} from "./workspaceDockStore";

export function WorkspaceQuickDock() {
  const t = useI18n((s) => s.t);
  const { pathname } = useLocation();
  const viewMode = useViewModeStore((s) => s.viewMode);
  const favourites = useWorkspaceDockStore((s) => s.favourites);
  const pin = useWorkspaceDockStore((s) => s.pin);
  const unpin = useWorkspaceDockStore((s) => s.unpin);
  const close = useWorkspaceDockStore((s) => s.close);
  const add = useWorkspaceDockStore((s) => s.add);
  const reorder = useWorkspaceDockStore((s) => s.reorder);
  const [dragId, setDragId] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const dragFrom = useRef<string | null>(null);

  const items = favourites.filter((i) => isRouteAllowedForViewMode(i.route, viewMode));
  const available = DOCK_CATALOG.filter(
    (c) =>
      isRouteAllowedForViewMode(c.route, viewMode) && !favourites.some((f) => f.id === c.id),
  );

  if (!items.length && !available.length) return null;

  function onDragStart(id: string) {
    dragFrom.current = id;
    setDragId(id);
  }

  function onDrop(targetId: string) {
    const from = dragFrom.current;
    dragFrom.current = null;
    setDragId(null);
    if (from) reorder(from, targetId);
  }

  return (
    <nav
      className="ews-workspace-dock ews-hierarchy-nav"
      aria-label={t("dock.workspace")}
      data-testid="workspace-quick-dock"
    >
      <span className="ews-workspace-dock-label eds-type-caption">{t("dock.favourites")}</span>
      <ul className="ews-workspace-dock-list">
        {items.map((item) => {
          const active =
            pathname === item.route ||
            pathname.startsWith(`${item.route}/`) ||
            pathname.startsWith(item.route.split("?")[0]!);
          return (
            <li
              key={item.id}
              className={cn("ews-workspace-dock-item", dragId === item.id && "is-dragging")}
              draggable
              onDragStart={() => onDragStart(item.id)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => onDrop(item.id)}
              onDragEnd={() => {
                dragFrom.current = null;
                setDragId(null);
              }}
            >
              <Link
                to={item.route}
                className={cn("ews-workspace-dock-chip", active && "is-active", item.pinned && "is-pinned")}
                title={item.label}
              >
                {item.pinned ? "📌 " : null}
                {item.label}
              </Link>
              <span className="ews-workspace-dock-ops">
                <button
                  type="button"
                  className="ews-dock-mini"
                  aria-label={item.pinned ? t("dock.unpin") : t("dock.pinFav")}
                  title={item.pinned ? t("dock.unpin") : t("dock.pinFav")}
                  onClick={() => (item.pinned ? unpin(item.id) : pin(item.id))}
                >
                  {item.pinned ? "★" : "☆"}
                </button>
                {!item.pinned ? (
                  <button
                    type="button"
                    className="ews-dock-mini"
                    aria-label={t("dock.close")}
                    title={t("dock.close")}
                    onClick={() => close(item.id)}
                  >
                    ×
                  </button>
                ) : null}
              </span>
            </li>
          );
        })}
      </ul>
      <div className="ews-workspace-dock-add">
        <Button size="sm" variant="ghost" onClick={() => setPickerOpen((v) => !v)} data-testid="dock-add">
          {pickerOpen ? t("dock.hideAdd") : t("dock.add")}
        </Button>
        {pickerOpen && available.length ? (
          <ul className="ews-workspace-dock-picker">
            {available.map((c: DockFavourite) => (
              <li key={c.id}>
                <button
                  type="button"
                  className="ews-workspace-dock-chip"
                  onClick={() => {
                    add(c);
                    setPickerOpen(false);
                  }}
                >
                  + {c.label}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </nav>
  );
}
