/**
 * Prompt Studio panel — Sprint 28.3.
 * Collections · categories · variables · versioning · search · favorites.
 */

import { Badge, Button, Card, Input } from "@/ui";
import { PROMPT_CATEGORIES } from "./productionCatalog";
import { useProductionStore } from "./productionStore";

export function PromptStudioPanel() {
  const q = useProductionStore((s) => s.promptQuery);
  const setQ = useProductionStore((s) => s.setPromptQuery);
  const cat = useProductionStore((s) => s.promptCategory);
  const setCat = useProductionStore((s) => s.setPromptCategory);
  const filtered = useProductionStore((s) => s.filteredPrompts);
  const collections = useProductionStore((s) => s.promptCollections);
  const toggle = useProductionStore((s) => s.togglePromptFavorite);
  const bump = useProductionStore((s) => s.bumpPromptVersion);
  const list = filtered();

  return (
    <div className="stack-md">
      <Card title="Prompt Collections">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {collections.map((c) => (
            <button
              key={c.id}
              type="button"
              className="ews-glass"
              style={{ textAlign: "left", padding: 12, borderRadius: "var(--eds-radius-xl)", cursor: "pointer" }}
              onClick={() => setCat(c.category)}
            >
              <p className="font-medium">{c.title}</p>
              <p className="eds-type-helper">{c.description}</p>
              <Badge>{c.promptIds.length} prompts</Badge>
            </button>
          ))}
        </div>
      </Card>
      <Card title="Prompt Studio">
        <div className="row mb-3" style={{ gap: 6, flexWrap: "wrap" }}>
          <Button size="sm" variant={cat === "all" ? "primary" : "ghost"} toolbar onClick={() => setCat("all")}>
            All
          </Button>
          {PROMPT_CATEGORIES.map((c) => (
            <Button key={c} size="sm" variant={cat === c ? "primary" : "ghost"} toolbar onClick={() => setCat(c)}>
              {c}
            </Button>
          ))}
        </div>
        <Input placeholder="Search prompts, tags, variables…" value={q} onChange={(e) => setQ(e.target.value)} />
        <ul className="stack-sm mt-3">
          {list.map((p) => (
            <li key={p.id} className="ews-glass" style={{ padding: 12, borderRadius: "var(--eds-radius-lg)" }}>
              <div className="row" style={{ justifyContent: "space-between", gap: 8 }}>
                <div>
                  <p className="font-medium">
                    {p.favorite ? "★ " : ""}
                    {p.title}
                  </p>
                  <p className="eds-type-helper">
                    {p.category} · v{p.version} · template · {p.tags.join(", ")}
                  </p>
                </div>
                <div className="row" style={{ gap: 6 }}>
                  <Button size="sm" variant="ghost" onClick={() => toggle(p.id)}>
                    Favorite
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => bump(p.id, `${p.body}\n# revise ${new Date().toISOString().slice(0, 10)}`)}
                  >
                    New version
                  </Button>
                </div>
              </div>
              <pre className="eds-type-small mt-2" style={{ whiteSpace: "pre-wrap", opacity: 0.9 }}>
                {p.body}
              </pre>
              <p className="eds-type-helper mt-1">Variables: {p.variables.map((v) => `{{${v}}}`).join(" ")}</p>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
