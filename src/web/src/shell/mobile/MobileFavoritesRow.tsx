import { useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { useViewModeStore, isRouteAllowedForViewMode } from "@/ux-revolution";
import { DOCK_CATALOG, useWorkspaceDockStore } from "@/workspace-chrome";
import { useMobileChromeStore } from "./mobileChromeStore";
import { closeMobileOverlay, navigateFromMobileOverlay } from "./useMobileOverlayHistory";

export function MobileFavoritesRow() {
  const viewMode = useViewModeStore((s) => s.viewMode);
  const favourites = useWorkspaceDockStore((s) => s.favourites);
  const open = useMobileChromeStore((s) => s.favoritesOpen);
  const setFavoritesOpen = useMobileChromeStore((s) => s.setFavoritesOpen);
  const navigate = useNavigate();
  const items = favourites.filter((i) => isRouteAllowedForViewMode(i.route, viewMode));
  const catalog = DOCK_CATALOG.filter((c) => isRouteAllowedForViewMode(c.route, viewMode));
  const count = items.length || catalog.length;

  return (
    <>
      <button
        type="button"
        className="ados-mobile-fav"
        data-testid="mobile-favorites-row"
        onClick={() => setFavoritesOpen(true)}
      >
        <span>⭐ Избранное</span>
        <span>
          {count} &gt;
        </span>
      </button>
      {open ? (
        <>
          <button type="button" className="ados-mobile-overlay" aria-label="Закрыть избранное" onClick={closeMobileOverlay} />
          <div className="ados-mobile-sheet" data-testid="mobile-favorites-sheet" role="dialog">
            <div className="ados-mobile-sheet__head">
              <h2 className="font-semibold">Избранное</h2>
              <Button size="sm" variant="ghost" onClick={closeMobileOverlay}>
                Закрыть
              </Button>
            </div>
            <div className="ados-mobile-sheet__body flex flex-col gap-1">
              {(items.length ? items : catalog).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="flex min-h-11 items-center rounded-md px-3 py-2 text-left"
                  onClick={() => navigateFromMobileOverlay(navigate, item.route)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </>
  );
}
