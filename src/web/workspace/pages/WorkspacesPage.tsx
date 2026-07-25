import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card } from "@/ui";
import { workspaceManager } from "../managers";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function WorkspacesPage() {
  const [active, setActive] = useState(workspaceManager.active());
  const navigate = useNavigate();

  return (
    <WorkspaceLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Workspace Manager</h1>
        <p className="eds-type-small">Kinds: {workspaceManager.kinds().join(", ")}</p>
        <div className="eds-grid eds-grid--dashboard">
          {workspaceManager.list().map((w) => (
            <Card key={w.workspaceId} title={w.name}>
              <Badge>{w.kind}</Badge>
              <p className="mt-2 eds-type-caption">Owner: {w.owner}</p>
              <p className="eds-type-caption">Org: {w.organization}</p>
              <p className="eds-type-caption">Modules: {w.activeModules.join(", ")}</p>
              <p className="eds-type-caption">Theme: {w.theme} · {w.status}</p>
              <Button
                className="mt-3"
                size="sm"
                variant={active.workspaceId === w.workspaceId ? "primary" : "secondary"}
                onClick={() => {
                  setActive(workspaceManager.setActive(w.workspaceId));
                  navigate("/workspace");
                }}
              >
                {active.workspaceId === w.workspaceId ? "Active" : "Switch"}
              </Button>
            </Card>
          ))}
        </div>
      </div>
    </WorkspaceLayout>
  );
}
