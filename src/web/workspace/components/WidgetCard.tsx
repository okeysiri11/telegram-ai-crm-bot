import { Card, Badge, Button } from "@/ui";
import type { WidgetInstance } from "../types";
import { widgetManager } from "../managers";

export function WidgetCard({
  widget,
  onChange,
}: {
  widget: WidgetInstance;
  onChange?: () => void;
}) {
  return (
    <Card title={widget.title} className="eds-anim-fade">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge>{widget.kind}</Badge>
        {widget.realtime ? <Badge tone="success">live</Badge> : null}
        <span className="eds-type-caption">
          {widget.w}×{widget.h} @ ({widget.x},{widget.y})
        </span>
      </div>
      <p className="eds-type-small text-[var(--eds-text-muted)]">
        Configurable widget · drag/resize ready · refresh {String(widget.config.refreshSec ?? 60)}s
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            widgetManager.move(widget.widgetId, (widget.x + 1) % 12, widget.y);
            onChange?.();
          }}
        >
          Move
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            widgetManager.resize(widget.widgetId, Math.min(12, widget.w + 1), widget.h);
            onChange?.();
          }}
        >
          Resize
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            widgetManager.configure(widget.widgetId, { refreshSec: 15 });
            onChange?.();
          }}
        >
          Configure
        </Button>
      </div>
    </Card>
  );
}
