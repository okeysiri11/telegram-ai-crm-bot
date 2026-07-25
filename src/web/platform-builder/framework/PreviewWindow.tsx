import { Card } from "@/ui";

export function PreviewWindow({
  title,
  summary,
  payload,
}: {
  title: string;
  summary: string;
  payload?: Record<string, unknown>;
}) {
  return (
    <Card title={`Preview · ${title}`}>
      <p className="eds-type-small text-[var(--eds-text-muted)]">{summary}</p>
      {payload ? (
        <pre className="mt-3 max-h-48 overflow-auto rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] p-3 eds-type-caption">
          {JSON.stringify(payload, null, 2)}
        </pre>
      ) : null}
    </Card>
  );
}
