import { useState } from "react";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Button, Card } from "@/ui";
import { layoutManager, widgetManager, workspaceManager } from "../managers";
import { WidgetCard } from "../components/WidgetCard";

export function LayoutEditorPage() {
  const ws = workspaceManager.active();
  const [widgets, setWidgets] = useState(widgetManager.list());
  const refresh = () => setWidgets(widgetManager.list());

  return (
    <WorkspaceLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Layout Manager</h1>
        <p className="eds-type-small">{layoutManager.features().join(" · ")}</p>
        <Button
          onClick={() => {
            layoutManager.save(ws.workspaceId, widgetManager.list());
            refresh();
          }}
        >
          Save layout
        </Button>
        <Card title="Responsive grid · docking · multi-monitor ready">
          <div className="eds-grid eds-grid--responsive gap-4">
            {widgets.map((w) => (
              <div key={w.widgetId} className="col-span-12 md:col-span-6 xl:col-span-4">
                <WidgetCard widget={w} onChange={refresh} />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
