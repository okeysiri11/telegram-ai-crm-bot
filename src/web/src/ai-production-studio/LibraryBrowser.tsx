/**
 * Library browser — templates · assets · media — Sprint 28.3.
 */

import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import type { MediaKind } from "./productionCatalog";
import { useProductionStore } from "./productionStore";

export function LibraryBrowser({ mode = "all" }: { mode?: "all" | "templates" | "assets" | "media" }) {
  const filter = useProductionStore((s) => s.mediaFilter);
  const setFilter = useProductionStore((s) => s.setMediaFilter);
  const media = useProductionStore((s) => s.filteredMedia)();
  const addMedia = useProductionStore((s) => s.addMedia);

  const kinds: (MediaKind | "all")[] =
    mode === "templates"
      ? ["template"]
      : mode === "assets"
        ? ["brand", "font", "icon", "document"]
        : mode === "media"
          ? ["image", "video", "audio", "animation"]
          : ["all", "image", "video", "audio", "document", "template", "brand", "font", "icon", "animation"];

  const list =
    mode === "templates"
      ? media.filter((m) => m.kind === "template")
      : mode === "assets"
        ? media.filter((m) => ["brand", "font", "icon", "document"].includes(m.kind))
        : mode === "media"
          ? media.filter((m) => ["image", "video", "audio", "animation"].includes(m.kind))
          : media;

  return (
    <Card
      title={
        mode === "templates"
          ? "Template Library"
          : mode === "assets"
            ? "Asset Library"
            : mode === "media"
              ? "Media Browser"
              : "Library Browser"
      }
    >
      <div className="row" style={{ gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
        {kinds.map((k) => (
          <Button key={k} size="sm" variant={filter === k ? "primary" : "ghost"} toolbar onClick={() => setFilter(k)}>
            {k}
          </Button>
        ))}
        <Button
          size="sm"
          variant="secondary"
          onClick={() =>
            addMedia({
              name: mode === "templates" ? "New template" : "New asset",
              kind: mode === "templates" ? "template" : "image",
              studioId: mode === "templates" ? "templates" : "assets",
              tags: [mode],
              status: "draft",
            })
          }
        >
          Add
        </Button>
        <Link to="/platform-builder/assets">
          <Button size="sm" variant="ghost">
            Asset Registry
          </Button>
        </Link>
      </div>
      <ul className="stack-sm">
        {list.map((m) => (
          <li key={m.id} className="row" style={{ justifyContent: "space-between", gap: 8 }}>
            <span>
              <strong>{m.name}</strong>
              <span className="eds-type-helper">
                {" "}
                · {m.kind} · {m.studioId}
              </span>
            </span>
            <span className="row" style={{ gap: 6 }}>
              <Badge>{`v${m.version}`}</Badge>
              <Badge tone={m.status === "approved" ? "success" : m.status === "archived" ? "default" : "warning"}>
                {m.status}
              </Badge>
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
