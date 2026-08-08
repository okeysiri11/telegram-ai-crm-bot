import { RuntimeHealthWidget } from "./RuntimeHealthWidget";
import { DockPanel } from "./DockPanel";
import { useShellLayoutStore } from "./shellLayoutStore";
import { Button } from "@/ui";
import { useI18n } from "@/i18n";

/**
 * Sprint 27.4 / 41.3 — bottom dock hosts live Runtime Health (localized).
 */
export function BottomDock() {
  const t = useI18n((s) => s.t);
  const open = useShellLayoutStore((s) => s.docks.bottom.open);
  const setDock = useShellLayoutStore((s) => s.setDock);

  if (!open) {
    return (
      <div className="ews-bottom-dock-peek">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setDock("bottom", { open: true, collapsed: false })}
          aria-label={t("runtime.openBottom")}
        >
          {t("runtime.health")} ▴
        </Button>
      </div>
    );
  }

  return (
    <DockPanel side="bottom" title={t("runtime.health")} subtitle={t("runtime.healthSubtitle")}>
      <RuntimeHealthWidget compact />
    </DockPanel>
  );
}
