import { useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Button, Card, Input, Badge } from "@/ui";
import { dashboardEngine, workspaceManager } from "../managers";

export function DashboardsPage() {
  const [name, setName] = useState("My Custom Dashboard");
  const [list, setList] = useState(dashboardEngine.list());
  const ws = workspaceManager.active();

  return (
    <WorkspaceLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Dashboard Engine</h1>
        <p className="eds-type-small text-[var(--eds-text-muted)]">
          Kinds: {dashboardEngine.kinds().join(", ")}
        </p>
        <Card title="Create custom dashboard">
          <div className="flex flex-wrap gap-2">
            <Input value={name} onChange={(e) => setName(e.target.value)} />
            <Button
              onClick={() => {
                dashboardEngine.createCustom(name, ws.workspaceId, ["w_kpi", "w_ai", "w_tasks"]);
                setList(dashboardEngine.list());
              }}
            >
              Create
            </Button>
          </div>
        </Card>
        <div className="eds-grid eds-grid--dashboard">
          {list.map((d) => (
            <Card key={d.dashboardId} title={d.name}>
              <Badge>{d.kind}</Badge>
              <p className="mt-2 eds-type-caption">Workspace: {d.workspaceId}</p>
              <p className="eds-type-caption">Widgets: {d.widgetIds.length}</p>
              <Link className="mt-2 inline-block eds-type-small text-[var(--eds-primary)]" to={`/workspace/dashboards/${d.dashboardId}`}>
                Open
              </Link>
            </Card>
          ))}
        </div>
      </div>
    </WorkspaceLayout>
  );
}
