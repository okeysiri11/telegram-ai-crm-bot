import { RuntimeHealthWidget } from "./RuntimeHealthWidget";
import { DockPanel } from "./DockPanel";
import { useShellLayoutStore } from "./shellLayoutStore";
import { Button } from "@/ui";

/**
 * Sprint 27.4 — bottom dock hosts live Runtime Health (window size persisted).
 */
export function BottomDock() {
  const open = useShellLayoutStore((s) => s.docks.bottom.open);
  const setDock = useShellLayoutStore((s) => s.setDock);

  if (!open) {
    return (
      <div className="ews-bottom-dock-peek">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setDock("bottom", { open: true, collapsed: false })}
          aria-label="Open bottom dock"
        >
          Runtime Health ▴
        </Button>
      </div>
    );
  }

  return (
    <DockPanel side="bottom" title="Runtime Health" subtitle="Live probes · Frontend · Backend · AI · MCP">
      <RuntimeHealthWidget compact />
    </DockPanel>
  );
}
