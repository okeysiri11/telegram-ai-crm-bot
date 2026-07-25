import { Badge, Button, Card } from "@/ui";

type Props = {
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  busy?: boolean;
};

/** Reusable confirmation screen for Universal Builder Framework. */
export function ConfirmationScreen({
  title = "Confirm",
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
  busy,
}: Props) {
  return (
    <Card title={title}>
      <p className="eds-type-small text-[var(--eds-text-muted)]">{message}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {onCancel ? (
          <Button variant="ghost" disabled={busy} onClick={onCancel}>
            {cancelLabel}
          </Button>
        ) : null}
        {onConfirm ? (
          <Button variant="primary" disabled={busy} onClick={onConfirm}>
            {busy ? "Working…" : confirmLabel}
          </Button>
        ) : null}
      </div>
      <div className="mt-3">
        <Badge>Confirmation Screen</Badge>
      </div>
    </Card>
  );
}
