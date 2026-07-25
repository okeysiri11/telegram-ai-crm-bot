import { Badge, Card } from "@/ui";

type Props = {
  errors?: { field?: string; message: string; rule?: string }[];
  suggestions?: string[];
  ok?: boolean;
};

/** Live validation panel for Universal Builder Framework. */
export function LiveValidation({ errors = [], suggestions = [], ok }: Props) {
  return (
    <Card title="Live Validation">
      <div className="flex flex-wrap gap-2">
        <Badge>{ok ? "Valid" : "Needs attention"}</Badge>
        <Badge>Errors · {errors.length}</Badge>
        <Badge>Suggestions · {suggestions.length}</Badge>
      </div>
      {errors.length ? (
        <ul className="mt-3 space-y-1 eds-type-small text-[var(--eds-danger)]">
          {errors.map((e, i) => (
            <li key={`${e.field || "err"}-${i}`}>
              {e.field ? `${e.field}: ` : ""}
              {e.message}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 eds-type-small text-[var(--eds-text-muted)]">No live errors detected.</p>
      )}
      {suggestions.length ? (
        <ul className="mt-2 space-y-1 eds-type-caption text-[var(--eds-text-muted)]">
          {suggestions.map((s) => (
            <li key={s}>Suggestion: {s}</li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}
