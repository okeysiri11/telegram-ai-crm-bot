import { Badge, Button } from "@/ui";
import { useRuntimeHealth, type RuntimeHealthId } from "./useRuntimeHealth";

const ORDER: RuntimeHealthId[] = [
  "frontend",
  "runtime",
  "api",
  "ai",
  "providers",
  "memory",
  "voice",
  "mcp",
];

function toneBadge(tone: string): "success" | "warning" | "danger" | "default" {
  if (tone === "ok") return "success";
  if (tone === "warn") return "warning";
  if (tone === "err") return "danger";
  return "default";
}

/** Live Runtime Health widget — shared poller with StatusBar. */
export function RuntimeHealthWidget({ compact = false }: { compact?: boolean }) {
  const { items, updatedAt, refresh } = useRuntimeHealth(20_000);
  const byId = new Map(items.map((i) => [i.id, i]));
  const shown = ORDER.map((id) => byId.get(id)).filter(Boolean);

  return (
    <section className={compact ? "ews-health ews-health--compact" : "ews-health"} aria-label="Runtime Health">
      <div className="ews-health-head">
        <p className="eds-type-small font-medium">Live status</p>
        <div className="flex items-center gap-2">
          {updatedAt ? (
            <span className="eds-type-helper">{new Date(updatedAt).toLocaleTimeString()}</span>
          ) : null}
          <Button size="sm" variant="ghost" onClick={() => void refresh()}>
            Refresh
          </Button>
        </div>
      </div>
      <ul className={compact ? "ews-health-grid ews-health-grid--compact" : "ews-health-grid"}>
        {shown.map((item) =>
          item ? (
            <li key={item.id} className="ews-health-item" title={`${item.label}: ${item.detail}`}>
              <span className={`ews-dot ews-dot--${item.tone}`} aria-hidden />
              <span className="ews-health-label">{item.label}</span>
              <Badge tone={toneBadge(item.tone)}>{item.detail}</Badge>
            </li>
          ) : null,
        )}
      </ul>
    </section>
  );
}
