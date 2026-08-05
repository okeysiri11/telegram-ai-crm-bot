/**
 * Generation history + favorites — Sprint 28.3.
 */

import { Badge, Button, Card } from "@/ui";
import { useProductionStore } from "./productionStore";

export function GenerationHistoryPanel() {
  const generations = useProductionStore((s) => s.generations);
  const favGens = useProductionStore((s) => s.favoriteGenerations);
  const favPrompts = useProductionStore((s) => s.favoritePrompts);
  const favProjects = useProductionStore((s) => s.favoriteProjects);
  const setView = useProductionStore((s) => s.setView);

  return (
    <div className="stack-md">
      <Card title="Generation History">
        <ul className="stack-sm">
          {generations.map((g) => (
            <li key={g.id} className="row" style={{ justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
              <div>
                <p className="eds-type-small font-medium">
                  {g.favorite ? "★ " : ""}
                  {g.title}
                </p>
                <p className="eds-type-helper">
                  {g.studioId} · jobs {g.jobIds.length} · {g.agents.slice(0, 2).join(", ")}
                </p>
              </div>
              <Badge
                tone={
                  g.status === "done" ? "success" : g.status === "failed" ? "danger" : g.status === "running" ? "info" : "default"
                }
              >
                {g.status}
              </Badge>
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Favorites">
        <p className="eds-type-caption">Projects</p>
        <ul className="stack-sm mb-3">
          {favProjects().map((p) => (
            <li key={p.id} className="eds-type-small">
              ★ {p.title}
            </li>
          ))}
          {!favProjects().length ? <li className="eds-type-helper">None</li> : null}
        </ul>
        <p className="eds-type-caption">Prompts</p>
        <ul className="stack-sm mb-3">
          {favPrompts().map((p) => (
            <li key={p.id} className="eds-type-small">
              ★ {p.title}
            </li>
          ))}
        </ul>
        <p className="eds-type-caption">Generations</p>
        <ul className="stack-sm">
          {favGens().map((g) => (
            <li key={g.id} className="eds-type-small">
              ★ {g.title}
            </li>
          ))}
        </ul>
        <div className="mt-3">
          <Button size="sm" variant="ghost" onClick={() => setView("projects")}>
            Open projects
          </Button>
        </div>
      </Card>
    </div>
  );
}
