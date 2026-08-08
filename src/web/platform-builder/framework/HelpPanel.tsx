import { Badge, Card, Tooltip } from "@/ui";
import type { HelpContent } from "../types";
import { term } from "@/i18n/platformGlossary";

export function HelpPanel({ help, guided }: { help: HelpContent; guided?: boolean }) {
  return (
    <Card title={help.popup.title}>
      <div className="space-y-2 eds-type-small">
        <p>
          <Tooltip label={help.tooltip}>
            <span className="underline decoration-dotted">{help.shortDescription}</span>
          </Tooltip>
        </p>
        {guided ? (
          <>
            <p className="text-[var(--eds-text-muted)]">{help.detailedExplanation}</p>
            <p>
              <Badge>{term("purpose")}</Badge> {help.purpose}
            </p>
            <p>
              <Badge>{term("benefits")}</Badge> {help.benefits}
            </p>
            <p>
              <Badge>{term("typicalUse")}</Badge> {help.typicalUse}
            </p>
            <p>
              <Badge>{term("businessValue")}</Badge> {help.businessValue}
            </p>
            <p className="rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface-muted,transparent)] p-2">
              {help.example}
            </p>
          </>
        ) : (
          <p className="text-[var(--eds-text-muted)]">{help.popup.body}</p>
        )}
      </div>
    </Card>
  );
}
