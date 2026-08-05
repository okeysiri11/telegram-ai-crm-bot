/**
 * Project explorer + dashboard — Sprint 28.3 / 33.2.1 stability.
 */

import { useMemo } from "react";
import { Badge, Button, Card } from "@/ui";
import { productionRuntime } from "@/enterprise-runtime/productionRuntime";
import { useProductionStore } from "./productionStore";
import { studioById } from "./productionCatalog";

export function ProjectExplorer() {
  const projects = useProductionStore((s) => s.projects);
  const recent = useProductionStore((s) => s.recentProjects);
  const openProject = useProductionStore((s) => s.openProject);
  const toggleFavorite = useProductionStore((s) => s.toggleProjectFavorite);
  const activeProjectId = useProductionStore((s) => s.activeProjectId);
  const createProject = useProductionStore((s) => s.createProject);
  const activeStudioId = useProductionStore((s) => s.activeStudioId);

  return (
    <div className="stack-md">
      <Card title="Project Explorer">
        <div className="row mb-3" style={{ gap: 8, flexWrap: "wrap" }}>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => createProject("Untitled project", activeStudioId || "creative")}
          >
            New project
          </Button>
          <span className="eds-type-helper">{projects.length} projects · recent {recent().length}</span>
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <p className="eds-type-caption mb-2">Recent</p>
            <ul className="stack-sm">
              {recent().map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    className="ews-glass"
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: 10,
                      borderRadius: "var(--eds-radius-lg)",
                      border:
                        activeProjectId === p.id ? "1px solid var(--eds-primary)" : "1px solid var(--eds-border)",
                      cursor: "pointer",
                    }}
                    onClick={() => openProject(p.id)}
                  >
                    <span className="font-medium">
                      {p.favorite ? "★ " : ""}
                      {p.title}
                    </span>
                    <span className="eds-type-helper block">
                      {studioById(p.studioId)?.label} · {p.status}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="eds-type-caption mb-2">All</p>
            <ul className="stack-sm">
              {projects.map((p) => (
                <li key={p.id} className="row" style={{ justifyContent: "space-between", gap: 8 }}>
                  <button type="button" className="eds-type-small text-left" onClick={() => openProject(p.id)}>
                    {p.title}
                  </button>
                  <Button size="sm" variant="ghost" onClick={() => toggleFavorite(p.id)}>
                    {p.favorite ? "★" : "☆"}
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>
      {activeProjectId ? <ProjectDashboard projectId={activeProjectId} /> : null}
    </div>
  );
}

export function ProjectDashboard({ projectId }: { projectId: string }) {
  // Do not call projectDashboard inside the selector — it returns a new object
  // every getSnapshot and triggers Maximum update depth (Sprint 33.2.1).
  const projects = useProductionStore((s) => s.projects);
  const pipelines = useProductionStore((s) => s.pipelines);
  const media = useProductionStore((s) => s.media);
  const generations = useProductionStore((s) => s.generations);
  const generate = useProductionStore((s) => s.generateInStudio);
  const dash = useMemo(
    () => useProductionStore.getState().projectDashboard(projectId),
    [projectId, projects, pipelines, media, generations],
  );
  const mon = productionRuntime.monitor();
  if (!dash.project) return null;
  const p = dash.project;

  return (
    <Card title={`Project · ${p.title}`}>
      <p className="eds-type-helper mb-3">{p.description || "No description"}</p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mb-4">
        <div className="ews-glass" style={{ padding: 10, borderRadius: "var(--eds-radius-lg)" }}>
          <p className="eds-type-caption">Pipeline status</p>
          <p className="font-semibold">{dash.pipelines[0]?.stage || "—"}</p>
        </div>
        <div className="ews-glass" style={{ padding: 10, borderRadius: "var(--eds-radius-lg)" }}>
          <p className="eds-type-caption">Queue status</p>
          <p className="font-semibold">{dash.queueDepth} active</p>
        </div>
        <div className="ews-glass" style={{ padding: 10, borderRadius: "var(--eds-radius-lg)" }}>
          <p className="eds-type-caption">Progress / ETA</p>
          <p className="font-semibold">{dash.etaSec || mon.analytics.estimatedClearSec}s</p>
        </div>
        <div className="ews-glass" style={{ padding: 10, borderRadius: "var(--eds-radius-lg)" }}>
          <p className="eds-type-caption">Outputs</p>
          <p className="font-semibold">{dash.media.length}</p>
        </div>
      </div>
      <div className="row mb-3" style={{ gap: 8 }}>
        <Button size="sm" onClick={() => generate(p.studioId, { projectId: p.id, multiAgent: true })}>
          Generate
        </Button>
        <Badge tone={p.status === "active" ? "info" : "default"}>{p.status}</Badge>
      </div>
      <p className="eds-type-caption">Output gallery</p>
      <ul className="stack-sm mt-2">
        {dash.media.map((m) => (
          <li key={m.id} className="eds-type-small">
            {m.name} · {m.kind} · v{m.version}
          </li>
        ))}
        {!dash.media.length ? <li className="eds-type-helper">No assets yet</li> : null}
      </ul>
      <p className="eds-type-caption mt-3">History</p>
      <ul className="stack-sm mt-2">
        {dash.generations.map((g) => (
          <li key={g.id} className="eds-type-small">
            {g.title} · {g.status} · agents {g.agents.join(", ")}
          </li>
        ))}
      </ul>
    </Card>
  );
}
